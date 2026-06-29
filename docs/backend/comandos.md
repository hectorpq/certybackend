# Comandos de Gestión (Management Commands)

## `regenerate_certs` — `certificados/management/commands/regenerate_certs.py`

### Propósito

Regenera certificados existentes que tienen PDFs inválidos o URLs placeholder y los reenvía por email con el PDF adjunto.

### Criterio de Selección

Certificados donde `pdf_url` esté vacío o comience con:
- `https://example.com`
- `https://certificates.example.com`

### Flujo

1. Busca el primer superusuario como admin
2. Identifica certificados con PDFs inválidos
3. Por cada certificado:
    - Resetea `status → "pending"` y `pdf_url → ""`
    - Genera PDF real via `cert.generate(generated_by=admin)`
    - Envía email con PDF adjunto via `cert.deliver(method="email", ...)`
4. Reporta resultados (éxito/error por certificado)

### Uso

```bash
python manage.py regenerate_certs
```

### Salida

```
================================================
REGENERAR TODOS LOS CERTIFICADOS
================================================
✓ Admin: admin@certypro.com

[1] Certificados a regenerar: 5

[1] Juan Pérez - Taller de Python
    ✅ Email enviado a juan@example.com - PDF ADJUNTADO
[2] María López - Introducción a Django
    ✅ Email enviado a maria@example.com - PDF ADJUNTADO

================================================
✅ COMPLETADO
================================================
```
