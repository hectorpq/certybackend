# Cumplimiento ISO/IEC 25010

La norma ISO/IEC 25010 define las características de calidad del producto software. A continuación se mapea la cobertura de Certy.

## Características de Calidad

### Funcionalidad
| Atributo | Cobertura | Evidencia |
|----------|-----------|-----------|
| Completitud funcional | ✅ | Todos los requisitos RF implementados |
| Corrección funcional | ✅ | Pruebas unitarias + integración |
| Pertinencia funcional | ✅ | Validado con historias de usuario |

### Fiabilidad
| Atributo | Implementación |
|----------|---------------|
| Madurez | Pruebas de carga con Locust |
| Disponibilidad | Docker + redundancia de servicios |
| Tolerancia a fallos | Reintentos de envío (email/WhatsApp) |
| Recuperabilidad | Procedimientos de respaldo y restauración |

### Usabilidad
| Atributo | Documentación |
|----------|---------------|
| Reconocibilidad | Manuales de usuario por rol |
| Aprendizaje | Guías de inicio rápido |
| Operabilidad | Interfaz React intuitiva |
| Protección contra errores | Validaciones en frontend y backend |

### Eficiencia
| Atributo | Implementación |
|----------|---------------|
| Comportamiento temporal | Tareas asíncronas con Celery |
| Uso de recursos | Optimización de consultas + Redis |

### Mantenibilidad
| Atributo | Documentación |
|----------|---------------|
| Modularidad | Arquitectura Django REST + React |
| Reusabilidad | Componentes UI reutilizables |
| Analizabilidad | SonarQube + logging de auditoría |
| Capacidad de modificación | GitFlow + code review |
| Capacidad de prueba | Estrategia de pruebas documentada |

### Seguridad
| Atributo | Documentación |
|----------|---------------|
| Confidencialidad | JWT + OAuth + roles |
| Integridad | Códigos QR + firmas digitales |
| No repudio | AuditLog de acciones críticas |
| Trazabilidad | Trazabilidad requisitos → código |

### Portabilidad
| Atributo | Implementación |
|----------|---------------|
| Adaptabilidad | Docker multi-entorno |
| Capacidad de instalación | Guías de instalación + setup scripts |
| Capacidad de reemplazo | API REST estandarizada |
