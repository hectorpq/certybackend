"""
Paquete CRISP-DM para CertyPro.

Implementa las 6 fases de la metodologia CRISP-DM aplicadas a la prediccion
de asistencia (attendance) de participantes inscritos en eventos de capacitacion.

Fases:
    1. Comprension del negocio  -> pipeline.business_understanding()
    2. Comprension de los datos -> data_source + pipeline.data_understanding()
    3. Preparacion de los datos  -> features.build_feature_matrix()
    4. Modelado                  -> model.train_models()
    5. Evaluacion                -> model.evaluate() / pipeline
    6. Despliegue                -> analytics.views + management command

El paquete es auto-contenido y reproducible: puede ejecutarse CON la base de
datos de Django (datos reales) o SIN ella (datos sinteticos deterministas).
"""

from .config import RANDOM_SEED, TARGET

__all__ = ["RANDOM_SEED", "TARGET"]
