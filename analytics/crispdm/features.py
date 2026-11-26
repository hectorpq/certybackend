"""
Preparacion de los datos (CRISP-DM fase 3).

Transforma el DataFrame crudo de inscripciones en la matriz de caracteristicas
lista para el modelado:

    - Deriva variables temporales (dia de semana, mes, anticipacion).
    - Enriquece con la API de feriados (near_holiday).
    - Calcula el historial del participante SIN fuga de informacion temporal
      (solo eventos anteriores a la fecha del evento actual).
    - Limpia valores faltantes.

Se evita deliberadamente usar `grade`, `certificate_sent` u otras variables que
solo se conocen DESPUES del evento (data leakage).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .config import FEATURE_COLUMNS, HOLIDAY_WINDOW_DAYS, TARGET
from .holidays_api import get_holiday_dates


def _add_holiday_flag(df: pd.DataFrame, holidays: set[date]) -> pd.DataFrame:
    """Marca si la fecha del evento cae a +/- N dias de un feriado."""
    holiday_set = set(holidays)

    def is_near(d: date) -> int:
        for delta in range(-HOLIDAY_WINDOW_DAYS, HOLIDAY_WINDOW_DAYS + 1):
            if (d + pd.Timedelta(days=delta)).date() in holiday_set:
                return 1
        return 0

    dates = pd.to_datetime(df["event_date"])
    df["near_holiday"] = [is_near(d) for d in dates]
    return df


def _add_participant_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Historial del participante ANTES de cada evento (sin leakage):
      - participant_prior_events: nro de inscripciones previas
      - participant_prior_rate:   tasa de asistencia previa (0.5 si no tiene historial)
    """
    df = df.sort_values("event_date").reset_index(drop=True)
    prior_events = []
    prior_rate = []
    seen_counts: dict[int, int] = {}
    seen_attended: dict[int, int] = {}

    for _, row in df.iterrows():
        pid = row["participant_id"]
        c = seen_counts.get(pid, 0)
        a = seen_attended.get(pid, 0)
        prior_events.append(c)
        prior_rate.append(a / c if c > 0 else 0.5)
        seen_counts[pid] = c + 1
        seen_attended[pid] = a + int(row["attended"])

    df["participant_prior_events"] = prior_events
    df["participant_prior_rate"] = prior_rate
    return df


def build_feature_matrix(
    raw: pd.DataFrame, *, use_network: bool = True
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Devuelve (X, y, df_enriquecido).

    X: solo las columnas FEATURE_COLUMNS.
    y: la variable objetivo TARGET.
    df_enriquecido: dataset completo con features (para EDA / plots).
    """
    df = raw.copy()
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["enrolled_at"] = pd.to_datetime(df["enrolled_at"])

    # Variables temporales.
    df["event_dow"] = df["event_date"].dt.dayofweek          # 0 = lunes
    df["event_month"] = df["event_date"].dt.month
    df["lead_time_days"] = (df["event_date"] - df["enrolled_at"]).dt.days.clip(lower=0)

    # Enriquecimiento con API externa de feriados.
    years = tuple(sorted(df["event_date"].dt.year.unique().tolist()))
    holidays = get_holiday_dates(years=years, use_network=use_network)
    df = _add_holiday_flag(df, holidays)

    # Historial del participante (sin leakage temporal).
    df = _add_participant_history(df)

    # Limpieza de faltantes en numericas.
    for col in ["duration_hours", "max_capacity", "lead_time_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET].astype(int)
    return X, y, df
