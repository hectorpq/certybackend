# Generación de PDFs (`services/pdf_service.py`)

## Motor de Renderizado

`PDFService` es el motor que genera los certificados PDF utilizando **ReportLab** como librería de renderizado. El servicio produce documentos en formato A4 apaisado (landscape).

## Flujo de Generación

- **Preparación del canvas:** Se crea un `reportlab.pdfgen.canvas.Canvas` con tamaño A4 apaisado (`841.89 x 595.28 puntos`).
- **Dibujo del fondo:** Se renderiza la imagen de fondo de la plantilla (`Template.background_image`) escalada al tamaño completo del PDF. Si no hay imagen, se dibuja un fondo predeterminado con borde azul marino y texto "CERTIFICADO / DE ASISTENCIA Y PARTICIPACIÓN".
- **Renderizado de campos de texto:** Se recorren las entradas del `layout_config` (JSON almacenado en `Template`). Cada campo (`participant_name`, `event_name`, `event_date`, `verification_code`) se renderiza con:
    - Coordenadas X/Y en pulgadas (desde `layout_config` o valores por defecto)
    - Tamaño de fuente, familia tipográfica y color
    - Centrado automático si la coordenada X supera la mitad del ancho
    - Ajuste de texto (`_fit_text`): trunca con "..." si el texto excede el ancho máximo disponible
- **Código QR de verificación:** Se genera un código QR usando la librería `qrcode` que apunta a la URL de verificación: `{CERTIFICATE_VERIFY_BASE_URL}/api/certificates/verify/?code={verification_code}`. El QR se ubica en la esquina inferior derecha con la etiqueta "Escanea para verificar".
- **Firma del instructor:** Se renderiza en la parte inferior central:
    - La imagen de firma digitalizada (`instructor.signature_image`) si existe
    - Una línea horizontal
    - El nombre del instructor y su especialidad
    - Si no hay instructor asociado al evento pero hay configuración de firma en `layout_config.signature`, se usa esa configuración ad-hoc
- **Guardado:** El PDF generado se guarda en `certificates/pdfs/{participant.id}_{event.id}_{verification_code}.pdf`. La ruta relativa se almacena en `Certificate.pdf_url`.

## Configuración desde la Plantilla

El campo `layout_config` del modelo `Template` es un diccionario JSON que controla la posición y estilo de cada elemento:

```json
{
  "participant_name": {
    "x": 100, "y": 150, "font_size": 28,
    "font_family": "Helvetica", "color": "#1e3a8a",
    "centered": true
  },
  "event_name": {
    "x": 100, "y": 200, "font_size": 18,
    "font_family": "Helvetica", "color": "#1e3a8a"
  },
  "event_date": {
    "x": 100, "y": 250, "font_size": 14,
    "font_family": "Helvetica", "color": "#94a3b8"
  },
  "verification_code": {
    "x": 50, "y": 50, "font_size": 9,
    "font_family": "Helvetica", "color": "#64748b"
  },
  "qr_code": {
    "x": 700, "y": 50, "size": 1.35
  },
  "signature": {
    "instructor_name": "Dr. Juan Pérez",
    "instructor_specialty": "Director Académico",
    "line_y": 1.05, "name_y": 0.70
  }
}
```

## Generación Masiva

`PDFService.generate_bulk_pdfs(certificates)` permite generar PDFs para múltiples certificados de forma iterativa. Retorna un resumen con cantidad de generados exitosamente y errores.
