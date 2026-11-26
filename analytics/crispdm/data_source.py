"""
Fuente de datos (CRISP-DM fase 2: Comprension de los datos).

Construye un DataFrame a nivel de INSCRIPCION (Enrollment), que es la unidad de
analisis: cada fila es "un participante inscrito en un evento" y la etiqueta es
si asistio o no (`attended`).

Dos modos:
    - from_orm():      lee datos reales desde la base de datos Django.
    - from_synthetic(): genera datos sinteticos deterministas (seed fija) con
                        una estructura identica a la real. Permite ejecutar y
                        REPLICAR el analisis sin necesidad de la base de datos.

El resto del pipeline no distingue el origen: ambos devuelven las mismas
columnas crudas.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from .config import RANDOM_SEED, YEARS

# Columnas crudas que produce cualquiera de los dos modos.
RAW_COLUMNS = [
    "enrollment_id",
    "participant_id",
    "event_id",
    "category",
    "duration_hours",
    "max_capacity",
    "is_public",
    "event_date",
    "enrolled_at",
    "was_invited",
    "invitation_accepted",
    "attended",
]

CATEGORIES = [
    "Tecnologia",
    "Gestion",
    "Idiomas",
    "Salud",
    "Educacion",
    "Finanzas",
]


def from_orm() -> pd.DataFrame:
    """Lee inscripciones reales desde el ORM de Django. Requiere Django configurado."""
    from events.models import Enrollment  # import diferido: solo si se usa ORM

    rows = []
    qs = (
        Enrollment.objects.select_related("event", "event__category", "invitation")
        .all()
    )
    for e in qs.iterator():
        ev = e.event
        if ev is None or ev.event_date is None:
            continue
        inv = e.invitation
        rows.append(
            {
                "enrollment_id": e.id,
                "participant_id": e.participant_id,
                "event_id": ev.id,
                "category": ev.category.name if ev.category else "SinCategoria",
                "duration_hours": ev.duration_hours or 0,
                "max_capacity": ev.max_capacity or 0,
                "is_public": int(bool(ev.is_public)),
                "event_date": ev.event_date,
                "enrolled_at": e.enrolled_at.date() if e.enrolled_at else ev.event_date,
                "was_invited": int(inv is not None),
                "invitation_accepted": int(bool(inv and inv.status == "accepted")),
                "attended": int(bool(e.attendance)),
            }
        )
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def from_synthetic(n_participants: int = 450, n_events: int = 70, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Genera inscripciones sinteticas deterministas.

    La asistencia NO es aleatoria pura: se simula con un modelo logistico latente
    sobre caracteristicas reales (anticipacion de inscripcion, duracion, feriados,
    fiabilidad del participante, invitacion). Asi el dataset contiene senal real
    que el modelo puede aprender, y los resultados son reproducibles (seed fija).
    """
    rng = np.random.default_rng(seed)
    start = date(YEARS[0], 1, 1)
    span_days = (date(YEARS[-1], 12, 31) - start).days

    # --- Participantes con una "fiabilidad" latente (propension a asistir) ---
    reliability = rng.beta(2.5, 2.0, size=n_participants)  # en [0,1], sesgo medio-alto

    # --- Eventos ---
    ev_category = rng.choice(CATEGORIES, size=n_events)
    ev_duration = rng.choice([4, 8, 16, 24, 40], size=n_events)
    ev_capacity = rng.choice([20, 30, 50, 80, 120], size=n_events)
    ev_public = rng.binomial(1, 0.5, size=n_events)
    ev_offset = rng.integers(0, span_days, size=n_events)
    ev_date = [start + timedelta(days=int(o)) for o in ev_offset]

    # Feriados fijos de Peru para la senal latente (la API real se usa luego en
    # features.py; aqui solo inyectamos el efecto para que exista correlacion).
    fixed_holidays = {(1, 1), (5, 1), (6, 29), (7, 28), (7, 29), (8, 30), (10, 8), (11, 1), (12, 8), (12, 25)}

    def near_holiday(d: date) -> bool:
        for delta in range(-2, 3):
            dd = d + timedelta(days=delta)
            if (dd.month, dd.day) in fixed_holidays:
                return True
        return False

    rows = []
    enrollment_id = 1
    for ev in range(n_events):
        # Numero de inscritos por evento (acotado por capacidad).
        n_enroll = int(min(ev_capacity[ev], rng.integers(10, 60)))
        attendees = rng.choice(n_participants, size=n_enroll, replace=False)
        edate = ev_date[ev]
        is_holiday = near_holiday(edate)

        for pid in attendees:
            # Anticipacion de la inscripcion (dias antes del evento).
            lead = int(rng.integers(0, 45))
            enrolled = edate - timedelta(days=lead)
            was_invited = int(rng.binomial(1, 0.7))
            inv_accepted = int(was_invited and rng.binomial(1, 0.6))

            # Modelo logistico latente de asistencia. Los coeficientes dan mas
            # peso a variables OBSERVABLES (anticipacion, duracion, feriado,
            # invitacion) para que el modelo pueda aprender la senal; la
            # fiabilidad oculta aporta un componente irreducible menor.
            z = (
                -0.3
                + 1.0 * (reliability[pid] - 0.5)         # fiabilidad del participante (parcialmente oculta)
                + 0.055 * lead                            # inscribirse con antelacion -> mas compromiso
                - 0.05 * ev_duration[ev]                  # eventos muy largos -> menos asistencia
                - 1.5 * is_holiday                        # cerca de feriado -> menos asistencia
                + 1.1 * inv_accepted                      # acepto invitacion -> mas probable
                + 0.6 * ev_public[ev]                     # eventos publicos
            )
            prob = 1.0 / (1.0 + np.exp(-z))
            attended = int(rng.random() < prob)

            rows.append(
                {
                    "enrollment_id": enrollment_id,
                    "participant_id": int(pid),
                    "event_id": ev + 1,
                    "category": ev_category[ev],
                    "duration_hours": int(ev_duration[ev]),
                    "max_capacity": int(ev_capacity[ev]),
                    "is_public": int(ev_public[ev]),
                    "event_date": edate,
                    "enrolled_at": enrolled,
                    "was_invited": was_invited,
                    "invitation_accepted": inv_accepted,
                    "attended": attended,
                }
            )
            enrollment_id += 1

    df = pd.DataFrame(rows, columns=RAW_COLUMNS)
    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def load_raw(prefer_orm: bool = True, min_rows: int = 200) -> tuple[pd.DataFrame, str]:
    """
    Carga datos crudos eligiendo la mejor fuente disponible.

    Intenta ORM si prefer_orm=True y Django esta disponible con suficientes filas;
    si no, cae a datos sinteticos. Devuelve (df, origen).
    """
    if prefer_orm:
        try:
            df = from_orm()
            if len(df) >= min_rows:
                return df, "orm"
        except Exception as exc:  # noqa: BLE001 - Django ausente o BD vacia
            print(f"  [data] ORM no disponible o insuficiente ({exc}); usando datos sinteticos.")
    df = from_synthetic()
    return df, "synthetic"
