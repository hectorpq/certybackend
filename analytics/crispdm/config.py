"""Configuracion central del pipeline CRISP-DM (rutas, semilla, constantes)."""

from pathlib import Path

# Reproducibilidad: una unica semilla gobierna generacion de datos y modelos.
RANDOM_SEED = 42

# Variable objetivo del problema de clasificacion binaria.
TARGET = "attended"

# Pais usado para consultar la API de feriados (Nager.Date). PE = Peru.
HOLIDAYS_COUNTRY = "PE"

# Rango de anios cubierto por los datos sinteticos / por la API de feriados.
YEARS = (2023, 2024, 2025)

# Ventana (en dias) para considerar que un evento "cae cerca" de un feriado.
HOLIDAY_WINDOW_DAYS = 2

# Rutas de salida (plots, metricas, modelo entrenado).
BASE_DIR = Path(__file__).resolve().parent.parent  # .../analytics
OUTPUTS_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"
PLOTS_DIR = OUTPUTS_DIR / "plots"
HOLIDAYS_CACHE = OUTPUTS_DIR / "holidays_cache.json"
MODEL_PATH = MODELS_DIR / "attendance_model.joblib"
METRICS_PATH = OUTPUTS_DIR / "metrics.json"

# Columnas de caracteristicas que entran al modelo (sin fuga de informacion:
# se excluye grade, certificate_sent, etc. que solo se conocen tras el evento).
NUMERIC_FEATURES = [
    "duration_hours",
    "max_capacity",
    "lead_time_days",
    "participant_prior_events",
    "participant_prior_rate",
    "event_dow",
    "event_month",
]
BINARY_FEATURES = [
    "is_public",
    "near_holiday",
    "was_invited",
    "invitation_accepted",
]
CATEGORICAL_FEATURES = ["category"]

FEATURE_COLUMNS = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES


def ensure_dirs() -> None:
    """Crea las carpetas de salida si no existen."""
    for d in (OUTPUTS_DIR, MODELS_DIR, PLOTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
