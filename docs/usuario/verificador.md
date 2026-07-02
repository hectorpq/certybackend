# Manual del Verificador (Público)

## Propósito

Cualquier persona puede verificar la autenticidad de un certificado sin necesidad de iniciar sesión.

## Cómo Verificar

1. Obtener el código de verificación del certificado
    - Está impreso en el PDF del certificado
    - Es un código alfanumérico único de 20 caracteres

2. Ir a la página de verificación pública:
    ```
    https://dominio/verify?code=XXXX-XXXX-XXXX-XXXX
    ```

3. El sistema mostrará:
    - ✅ **Certificado válido:** Nombre del participante, evento, fecha de emisión
    - ❌ **Certificado no encontrado:** Mensaje indicando que el código no es válido

## Endpoint API

```
GET /api/certificates/verify/?code=XXXX
```

Respuesta exitosa:
```json
{
    "status": "success",
    "message": "Certificado verificado correctamente",
    "certificate": {
        "participant": { "full_name": "Juan Pérez", ... },
        "event": { "name": "Taller de Python", ... },
        "verification_code": "XXXX",
        "issued_at": "2025-01-15T10:00:00Z"
    }
}
```

## Notas

- La verificación no requiere autenticación
- El código de verificación es único por certificado
- Los certificados eliminados (soft delete) no aparecen como válidos
