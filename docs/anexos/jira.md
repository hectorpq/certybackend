# Gestión de Proyecto con Jira / Scrum

## Proceso Scrum

### Roles
- **Product Owner**: Define requisitos y prioriza backlog
- **Scrum Master**: Facilita el proceso y remueve impedimentos
- **Development Team**: Implementa las historias de usuario

### Ceremonias
| Ceremonia | Frecuencia | Propósito |
|-----------|-----------|-----------|
| Sprint Planning | Cada 2 semanas | Planificar el sprint |
| Daily Standup | Diaria | Sincronizar avances |
| Sprint Review | Fin de sprint | Demo de funcionalidades |
| Sprint Retrospective | Fin de sprint | Mejora continua |

### Artefactos
- **Product Backlog**: Lista priorizada de historias de usuario
- **Sprint Backlog**: Historias seleccionadas para el sprint
- **Increment**: Funcionalidad completada y lista para producción

## Configuración de Jira

### Proyecto
- **Nombre**: Certy
- **Tipo**: Software Development (Scrum)
- **Key**: CERTY

### Estructura de Issues
| Tipo | Descripción |
|------|-------------|
| Epic | Funcionalidad mayor (ej: "Módulo de certificados") |
| Story | Historia de usuario |
| Task | Tarea técnica |
| Bug | Defecto reportado |
| Sub-task | Descomposición de tarea |

### Workflow
```
To Do → In Progress → In Review → Done
```

### Campos Personalizados
- **Severidad**: Critical, Major, Minor, Trivial
- **Área**: Backend, Frontend, Infra, Docs
- **Sprint**: Número de sprint asignado

## Reportes y Métricas

| Métrica | Propósito |
|---------|-----------|
| Velocity | Capacidad del equipo por sprint |
| Burndown chart | Progreso del sprint |
| Cumulative flow | Visualización del flujo de trabajo |
| Cycle time | Tiempo de completion de issues |
