# Cumplimiento ISO/IEC 12207

La norma ISO/IEC 12207 establece los procesos del ciclo de vida del software. A continuación se mapean los procesos cubiertos por Certy.

## Procesos Principales

### Adquisición y Suministro
| Requisito | Cobertura | Evidencia |
|-----------|-----------|-----------|
| Definición de requisitos | ✅ | Requisitos funcionales y no funcionales documentados |
| Selección de proveedor | N/A | Desarrollo interno |

### Desarrollo

| Proceso | Implementación | Documentación |
|---------|---------------|---------------|
| Análisis de requisitos | Requisitos funcionales y no funcionales | `requisitos/` |
| Diseño arquitectónico | Diagramas C4 + ADR | `arquitectura/` |
| Diseño detallado | Documentación técnica backend/frontend | `desarrollo/` y `backend/` |
| Codificación | Convenciones, GitFlow, code review | `desarrollo/` |
| Pruebas | Unitarias, integración, E2E, carga | `pruebas/` |
| Integración | CI/CD pipeline | `despliegue/pipeline.md` |

### Operación

| Proceso | Implementación |
|---------|---------------|
| Despliegue | Docker + GitHub Actions + Jenkins |
| Monitoreo | Logs de auditoría, delivery tracking |
| Soporte al usuario | Manuales por rol |

### Mantenimiento

| Proceso | Documentación |
|---------|---------------|
| Respaldo | `mantenimiento/respaldo.md` |
| Restauración | `mantenimiento/restauracion.md` |
| Actualización | `mantenimiento/actualizacion.md` |
| Versionado | `mantenimiento/versionado.md` |

## Procesos de Soporte

| Proceso | Estado |
|---------|--------|
| Documentación | ✅ Completa (MkDocs) |
| Gestión de configuración | ✅ Git + GitFlow |
| Aseguramiento de calidad | ✅ SonarQube + pruebas |
| Verificación | ✅ Pruebas automatizadas |
| Validación | ✅ E2E + revisión manual |
| Auditoría | ✅ Checklist SDLC |
