"""
Consumo de API externa — Nager.Date (https://date.nager.at).

API publica, gratuita y SIN API key que devuelve los feriados oficiales de un
pais y anio. Se usa en la fase de "Preparacion de los datos" de CRISP-DM para
enriquecer cada evento con la variable `near_holiday` (si el evento ocurre
cerca de un feriado nacional, hecho que suele reducir la asistencia).

Endpoint:
    GET https://date.nager.at/api/v3/PublicHolidays/{year}/{countryCode}

Diseno para REPLICABILIDAD:
    - Si hay internet, consulta la API y cachea el resultado en disco.
    - Si no hay internet (o la API falla), usa la cache local y, como ultimo
      recurso, una lista minima de feriados fijos de Peru. Asi el pipeline
      SIEMPRE corre de forma reproducible, con o sin conexion.
"""

from __future__ import annotations

import json
from datetime import date

import requests

from .config import HOLIDAYS_CACHE, HOLIDAYS_COUNTRY, YEARS, ensure_dirs

API_BASE = "https://date.nager.at/api/v3/PublicHolidays"
TIMEOUT = 8

# Respaldo offline: feriados nacionales fijos de Peru (mismos cada anio).
# Garantiza que la variable near_holiday exista aunque no haya red.
_PERU_FIXED = [
    (1, 1),    # Anio Nuevo
    (5, 1),    # Dia del Trabajo
    (6, 29),   # San Pedro y San Pablo
    (7, 28),   # Fiestas Patrias
    (7, 29),   # Fiestas Patrias
    (8, 30),   # Santa Rosa de Lima
    (10, 8),   # Combate de Angamos
    (11, 1),   # Todos los Santos
    (12, 8),   # Inmaculada Concepcion
    (12, 25),  # Navidad
]


def _load_cache() -> dict:
    if HOLIDAYS_CACHE.exists():
        try:
            return json.loads(HOLIDAYS_CACHE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    ensure_dirs()
    HOLIDAYS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def _fetch_year(year: int, country: str) -> list[str] | None:
    """Consulta la API para un anio. Devuelve lista de fechas ISO o None si falla."""
    url = f"{API_BASE}/{year}/{country}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return [item["date"] for item in data if "date" in item]
    except (requests.RequestException, ValueError, KeyError):
        return None


def _fallback_dates(year: int) -> list[str]:
    return [date(year, m, d).isoformat() for (m, d) in _PERU_FIXED]


def get_holiday_dates(
    years: tuple[int, ...] = YEARS,
    country: str = HOLIDAYS_COUNTRY,
    *,
    use_network: bool = True,
) -> set[date]:
    """
    Devuelve el conjunto de fechas de feriados para los anios indicados.

    Estrategia: API -> cache -> respaldo fijo. Reporta por consola la fuente
    usada (util para evidenciar el consumo de API en la presentacion).
    """
    cache = _load_cache()
    out: set[date] = set()

    for year in years:
        key = f"{country}-{year}"
        iso_dates: list[str] | None = None
        source = "cache"

        if use_network:
            iso_dates = _fetch_year(year, country)
            if iso_dates is not None:
                source = "api"
                cache[key] = iso_dates

        if iso_dates is None:
            iso_dates = cache.get(key)
            if iso_dates is None:
                iso_dates = _fallback_dates(year)
                source = "fallback"

        print(f"  [API feriados] {key}: {len(iso_dates)} feriados (fuente={source})")
        for iso in iso_dates:
            try:
                out.add(date.fromisoformat(iso[:10]))
            except ValueError:
                continue

    _save_cache(cache)
    return out


if __name__ == "__main__":
    # Prueba manual del consumo de API.
    dates = get_holiday_dates()
    print(f"Total feriados cargados: {len(dates)}")
