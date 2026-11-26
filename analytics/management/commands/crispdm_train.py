"""
Management command: entrena el modelo CRISP-DM desde Django.

    python manage.py crispdm_train                # usa datos reales si existen
    python manage.py crispdm_train --synthetic    # fuerza datos sinteticos
    python manage.py crispdm_train --offline       # no consulta la API de feriados
"""

from django.core.management.base import BaseCommand

from analytics.crispdm.pipeline import run_pipeline


class Command(BaseCommand):
    help = "Ejecuta el pipeline CRISP-DM y entrena el modelo de prediccion de asistencia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--synthetic",
            action="store_true",
            help="Fuerza el uso de datos sinteticos (ignora la base de datos).",
        )
        parser.add_argument(
            "--offline",
            action="store_true",
            help="No consulta la API de feriados (usa cache / respaldo local).",
        )

    def handle(self, *args, **options):
        prefer_orm = not options["synthetic"]
        use_network = not options["offline"]
        report = run_pipeline(prefer_orm=prefer_orm, use_network=use_network)
        best = report["best_model_name"]
        auc = report["results"][best]["roc_auc"]
        self.stdout.write(
            self.style.SUCCESS(
                f"\nEntrenamiento completado. Modelo: {best} (ROC-AUC={auc:.3f}). "
                f"Guardado en {report['model_path']}"
            )
        )
