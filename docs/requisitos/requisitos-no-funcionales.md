# Requisitos No Funcionales

## Rendimiento

| ID | Descripción |
|----|-------------|
| RNF-01 | La generación de un PDF individual debe completarse en menos de 5 segundos |
| RNF-02 | La carga y procesamiento de un Excel de hasta 1000 registros debe completarse en menos de 30 segundos |
| RNF-03 | El envío masivo de correos debe procesarse asíncronamente sin bloquear la UI |
| RNF-04 | La API debe responder en menos de 500ms para operaciones CRUD estándar (p95) |
| RNF-05 | El sistema debe soportar al menos 50 usuarios concurrentes |

## Seguridad

| ID | Descripción |
|----|-------------|
| RNF-10 | Las contraseñas deben almacenarse hasheadas (PBKDF2/bcrypt) |
| RNF-11 | Los tokens JWT deben tener expiración (8h access, 7d refresh) |
| RNF-12 | El acceso a recursos debe validarse por rol (admin, coordinador, participante) |
| RNF-13 | Las claves de API (SendGrid, WhatsApp) deben almacenarse en variables de entorno |
| RNF-14 | La verificación pública de certificados no requiere autenticación |

## Disponibilidad

| ID | Descripción |
|----|-------------|
| RNF-20 | El sistema debe estar disponible 24/7 con ventana de mantenimiento programada |
| RNF-21 | Las tareas fallidas de Celery deben reintentarse automáticamente (hasta 3 veces) |
| RNF-22 | La base de datos debe tener respaldos automatizados |

## Mantenibilidad

| ID | Descripción |
|----|-------------|
| RNF-25 | El código debe seguir PEP 8 (Python) y ESLint (TypeScript) |
| RNF-26 | La API debe documentarse con OpenAPI/Swagger |
| RNF-27 | Las pruebas unitarias deben cubrir al menos el 80% del código |
| RNF-28 | El proyecto debe usar GitFlow para gestión de ramas |

## Usabilidad

| ID | Descripción |
|----|-------------|
| RNF-30 | La interfaz debe ser responsiva (mobile-friendly) |
| RNF-31 | El flujo de carga masiva debe guiar al usuario en 4 pasos con retroalimentación |
| RNF-32 | Los errores deben mostrarse en lenguaje claro en la UI |

## Portabilidad

| ID | Descripción |
|----|-------------|
| RNF-35 | El sistema debe ejecutarse en contenedores Docker |
| RNF-36 | La configuración debe manejarse completamente vía variables de entorno |
