"""
Runner STANDALONE del pipeline CRISP-DM (sin necesidad de Django ni base de datos).

Pensado para REPLICABILIDAD: cualquier persona puede reproducir todo el analisis
con solo Python + las dependencias de requirements-analytics.txt.

Uso:
    cd SystemCertification/analytics
    pip install -r requirements-analytics.txt
    python run_crispdm.py              # datos sinteticos + API de feriados
    python run_crispdm.py --offline    # sin red (usa cache/respaldo de feriados)

Salidas:
    outputs/plots/*.png      graficos de las 6 fases
    outputs/metrics.json     metricas de los modelos
    models/attendance_model.joblib   modelo entrenado
"""

import argparse
import sys
from pathlib import Path

# Permite importar el paquete `crispdm` al correr el archivo directamente.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crispdm.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline CRISP-DM - Prediccion de asistencia CertyPro")
    parser.add_argument("--offline", action="store_true", help="No consultar la API de feriados.")
    args = parser.parse_args()

    # prefer_orm=False: en modo standalone no hay Django, se usan datos sinteticos.
    report = run_pipeline(prefer_orm=False, use_network=not args.offline)

    print("\n" + "#" * 70)
    print("  PIPELINE CRISP-DM COMPLETADO")
    print("#" * 70)
    print(f"  Modelo ganador : {report['best_model_name']}")
    print(f"  Origen de datos: {report['source']}")
    print("  Revisa outputs/plots/ y outputs/metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
