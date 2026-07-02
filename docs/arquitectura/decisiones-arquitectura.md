# Decisiones de Arquitectura (ADR)

## ADR-001: Uso de Django REST Framework en vez de FastAPI

- **Contexto:** Necesitábamos un framework maduro con ORM, admin panel, autenticación y permisos integrados
- **Decisión:** Django 5.2 + DRF 3.14
- **Consecuencias:** Mayor productividad inicial, ecosistema maduro, pero menos rendimiento puro que FastAPI. Compensado con Celery para tareas pesadas

## ADR-002: Carga Masiva Síncrona con Celery para PDF/Email

- **Contexto:** La carga de Excel podría ser síncrona para retroalimentación inmediata, pero la generación de PDFs y envío de correos debe ser asíncrona
- **Decisión:** Procesamiento síncrono del Excel (validación + creación de registros), generación de PDF y envío delegados a Celery
- **Consecuencias:** El usuario ve resultados inmediatos en pantalla; los procesos pesados corren en background con reintentos automáticos

## ADR-003: ReportLab en vez de WeasyPrint o wkhtmltopdf

- **Contexto:** Necesitábamos control pixel-perfect sobre la posición del nombre, QR y firma sobre una imagen de fondo
- **Decisión:** ReportLab + qrcode (Pillow)
- **Consecuencias:** Mayor control visual, sin dependencias de navegador headless, pero más código de layout manual

## ADR-004: Soft Delete en vez de Hard Delete

- **Contexto:** Los datos de certificados tienen valor auditor; no deben perderse
- **Decisión:** Todos los modelos principales heredan `is_deleted`, `deleted_at`, `deleted_by`
- **Consecuencias:** Los registros nunca se pierden, las consultas deben filtrar `is_deleted=False`, el tamaño de la BD crece pero es aceptable

## ADR-005: JWT con Refresh Token Rotation

- **Contexto:** Sesión stateless para API REST con diferentes roles de usuario
- **Decisión:** JWT con access_token (8h) + refresh_token (7d), refresh rotation activado
- **Consecuencias:** Sin estado de sesión en servidor, los tokens pueden revocarse por expiración, el refresh rotation mejora seguridad

## ADR-006: Interfaz Single Page Application (SPA)

- **Contexto:** Necesitábamos una experiencia de usuario fluida con navegación sin recargas completas
- **Decisión:** React 18 + Vite + TypeScript con React Router 6
- **Consecuencias:** Mayor complejidad de build que SSR, pero mejor experiencia UX. TanStack Query simplifica el estado del servidor

## ADR-007: Separación de Servicios de Comunicación

- **Contexto:** Cada canal de entrega (email, WhatsApp) tiene APIs y configuraciones distintas
- **Decisión:** Clases separadas (`EmailService`, `WhatsAppService`) con interfaz común
- **Consecuencias:** Fácil agregar nuevos canales, cada servicio se configura independientemente, las dependencias externas están aisladas

## ADR-008: Postresql como Base de Datos

- **Contexto:** Necesitábamos JSONB para layout_config, consultas avanzadas y confiabilidad transaccional
- **Decisión:** PostgreSQL 15
- **Consecuencias:** Soporte nativo de JSON, índices parciales, rendimiento sólido, pero mayor consumo de recursos que SQLite
