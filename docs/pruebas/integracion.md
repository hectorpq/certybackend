# Pruebas de Integración

## Backend (Django TestCase + DRF APIClient)

Las pruebas de integración verifican que los endpoints funcionan correctamente con la base de datos, la autenticación y los permisos.

### Tipos de Pruebas

**Autenticación:**
- Registro de usuario con datos válidos
- Login con credenciales correctas
- Login con contraseña incorrecta (401)
- Acceso a endpoint protegido sin token (401)
- Refresco de token

**Certificados:**
- CRUD completo via API
- Generación de PDF
- Entrega por email/whatsapp/link
- Verificación pública con código válido
- Verificación con código inválido (404)

**Eventos:**
- CRUD completo
- Inscripción de participantes
- Generación masiva de certificados
- Finalización de evento

**Permisos:**
- Admin puede crear/editar/eliminar
- Coordinador puede crear/editar
- Participante solo lectura
- Anónimo no puede acceder

### Ejemplo

```python
from rest_framework.test import APITestCase
from rest_framework import status

class TestCertificadosAPI(APITestCase):
    def test_listar_certificados_autenticado(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/certificates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```
