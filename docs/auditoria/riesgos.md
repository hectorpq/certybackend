# Matriz de Riesgos

## Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|:-----------:|:-------:|------------|
| Falla en servicio de email (SendGrid) | Media | Alto | Reintentos automáticos + cola de reprocesamiento |
| Falla en API de WhatsApp | Media | Alto | Fallback a email + reintentos |
| Caída de base de datos | Baja | Crítico | Respaldo diario + restauración documentada |
| Pérdida de datos | Baja | Crítico | Respaldos automatizados + PostgreSQL WAL |
| Degradación de rendimiento | Media | Medio | Redis cache + tareas asíncronas + Locust testing |
| Vulnerabilidad de seguridad | Media | Alto | Bandit + OWASP + JWT + OAuth |
| Falla en generación de PDF | Baja | Medio | Logging + reintentos + validación |

## Riesgos de Proyecto

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|:-----------:|:-------:|------------|
| Cambios en requisitos | Alta | Medio | Trazabilidad + historias de usuario flexibles |
| Cobertura de pruebas insuficiente | Media | Alto | Estrategia de pruebas + métricas |
| Documentación desactualizada | Media | Medio | MkDocs + revisiones periódicas |
| Rotación de personal | Baja | Medio | Documentación completa + code review |

## Riesgos de Auditoría

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|:-----------:|:-------:|------------|
| Evidencias insuficientes | Media | Alto | Checklist SDLC + carpetas de evidencia |
| Trazabilidad incompleta | Media | Alto | Matriz de trazabilidad |
| Falta de documentación operativa | Baja | Medio | Manuales de operación + mantenimiento |

## Plan de Respuesta

| Nivel | Acción |
|-------|--------|
| Crítico | Respuesta inmediata (< 4 h), escalar a coordinador |
| Alto | Respuesta en 24 h, plan de contingencia |
| Medio | Respuesta en 72 h, seguimiento semanal |
| Bajo | Monitoreo pasivo, revisión mensual |
