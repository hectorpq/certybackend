# Bienvenido a Certy

**Certy** es un Sistema de Gestión y Entrega Masiva de Certificados diseñado para instituciones educativas y organizadores de eventos académicos. Permite crear eventos, configurar plantillas visuales de certificados, cargar participantes masivamente desde Excel/CSV, generar PDFs personalizados con códigos QR de verificación y distribuirlos por correo electrónico o WhatsApp.

## Stack Tecnológico

- **Backend:** Django 5.2 + Django REST Framework 3.14
- **Frontend:** React 18 + Vite 5 + TypeScript 5 + TailwindCSS 3
- **Base de Datos:** PostgreSQL
- **Procesamiento Asíncrono:** Celery + Redis (broker)
- **Generación de PDFs:** ReportLab + qrcode (Pillow)
- **Correo:** SendGrid API
- **WhatsApp:** Meta Cloud API
- **Pruebas E2E:** Playwright
- **Calidad:** SonarQube (análisis estático)

## Flujo Global del Negocio

- **Creación de Eventos:** El coordinador crea un evento académico (curso, taller, seminario) definiendo fechas, ubicación, categoría e instructor.
- **Configuración Visual de Plantillas:** Se diseña la plantilla del certificado subiendo una imagen de fondo (PNG/JPG) y posicionando interactivamente el nombre del participante mediante un editor visual de coordenadas (X, Y).
- **Carga Masiva por Excel/CSV:** Se sube un archivo con los datos de los participantes (`full_name`, `email`, `document_id`). El sistema valida el formato y permite previsualizar y editar los registros antes de procesar.
- **Procesamiento Asíncrono:** El backend procesa cada fila del archivo: crea o actualiza participantes, los inscribe al evento y genera los certificados. Los errores por fila no detienen el proceso completo.
- **Generación de PDFs:** Cada certificado se renderiza como PDF con el nombre del participante, evento, fecha, código QR de verificación único y firma digitalizada del instructor.
- **Distribución Omnicanal:** Los certificados se entregan por correo electrónico (con PDF adjunto vía SendGrid), WhatsApp (con enlace vía Meta Cloud API) o mediante enlace público de descarga.

## Roles del Sistema

- **admin:** Acceso total a todos los recursos del sistema, incluyendo auditoría, exportación y gestión de usuarios.
- **coordinador:** Usuario operativo — gestiona certificados, eventos, participantes e instructores en el día a día.
- **participante:** Usuario final — visualiza solo sus propios certificados y eventos en los que está inscrito.

## Autenticación

La plataforma soporta dos modalidades de inicio de sesión:

- **Email y Contraseña:** Registro y login tradicional con JWT (access token de 8 horas, refresh token de 7 días).
- **Google OAuth2:** Inicio de sesión con cuenta de Google, con creación automática de usuario si es la primera vez.
