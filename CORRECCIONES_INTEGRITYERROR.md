# Corrección - IntegrityError al crear certificado en Admin

## Problema Original
```
IntegrityError: el valor nulo en la columna «event_id» de la relación 
«certificados_certificate» viola la restricción "not-null"
```

Esto ocurría cuando intentabas crear un certificado desde `/admin/certificados/certificate/add/`

## Causa Raíz
El formulario admin **no mostraba los campos editables** `student` y `event`, solo mostraba versiones readonly (`student_info`, `event_info`).

**Resultado:** Al guardar un certificado nuevo:
- ❌ `student_id` = null
- ❌ `event_id` = null
- ❌ `verification_code` = vacío
- 💥 Violaba la restricción NOT NULL

## Soluciones Implementadas

### 1️⃣ Campos Editables Durante Creación
**Archivo:** `certificados/admin.py`

```python
def get_readonly_fields(self, request, obj=None):
    """Student and event are editable only during creation"""
    base_readonly = ('id', 'issued_at', 'updated_at', 'verification_code_info', 'template_info', 'delivery_history')
    
    # Durante edición: student y event readonly (no se pueden cambiar)
    if obj:
        return base_readonly + ('student', 'event')
    
    # Durante creación: student y event editables
    return base_readonly
```

**Efecto:** Ahora puedes seleccionar student y event al crear.

### 2️⃣ Auto-Generación de Código de Verificación
**Archivo:** `certificados/models.py`

```python
def save(self, *args, **kwargs):
    """Auto-generate verification code if not set"""
    if not self.verification_code:
        self.verification_code = self.generate_verification_code(
            str(self.student.id), 
            str(self.event.id)
        )
    super().save(*args, **kwargs)
```

**Efecto:** El código de verificación se genera automáticamente durante el guardado.

### 3️⃣ Formulario Simplificado en Creación
**Archivo:** `certificados/admin.py`

Se agregó `get_fieldsets()` para mostrar un formulario más limpio durante la creación:

**Durante Creación:**
- ✅ Status (default: 'pending')
- ✅ Student (selector)
- ✅ Event (selector)
- ✅ Template (opcional)
- ✅ Expiration (opcional)

**Durante Edición:**
- Muestra todos los campos incluyendo:
  - Historial de entregas
  - Timestamps
  - Info del código de verificación
  - PDF y datos generados

## Flujo Operativo Ahora

### Crear Certificado
1. Click: **Certificados → Add Certificate**
2. Formulario simple:
   - **Status:** Pending (automático)
   - **Student:** Selecciona estudiante
   - **Event:** Selecciona evento
   - **Template:** (opcional)
   - **Expires At:** (opcional)
3. Click: **Save**
   - ✅ Se asigna student_id
   - ✅ Se asigna event_id
   - ✅ Se genera verification_code automáticamente
   - ✅ Se guarda en base de datos sin errores

### Editar Certificado
1. Click sobre um certificado existente
2. Los campos **Student** y **Event** ahora son **readonly**
   - Evita cambios accidentales
   - Mantiene la integridad de datos
3. Puedes editar:
   - Status
   - Template
   - PDF URL
   - Expiration date
4. Ver historial completo de entregas

## Validaciones

✅ `student` es requerido (NO puede ser null)
✅ `event` es requerido (NO puede ser null)  
✅ `verification_code` se genera automáticamente
✅ Unique constraint: (student, event) → sin duplicados
✅ Status default: 'pending'

## Cambios de Archivos

```
certificados/admin.py
├─ Agregado: get_readonly_fields() - lógica condicional
├─ Agregado: get_fieldsets() - formularios distintos para crear/editar
├─ Modificado: fieldsets - ahora usa get_fieldsets()
└─ Removido: campo student_info y event_info del fieldsets de creación

certificados/models.py
├─ Agregado: save() method - auto-genera verification_code
└─ Sin cambios en esquema de DB
```

## Testing

Para verificar que funciona:

1. Ve a `/admin/certificados/certificate/`
2. Click en **Add Certificate**
3. Completa:
   - Student: Selecciona cualquiera
   - Event: Selecciona cualquiera (debe tener enrollment)
   - Status: Pending (default)
4. Click: **Save**
5. ✅ Debe guardar sin error IntegrityError

## Próximos Pasos

Si quieres generar certificados batch desde el admin:

1. Ve a `/admin/certificados/certificate/`
2. Selecciona certificados con status "Pending"
3. Acción: **✅ Generate Certificates**
4. Listo - cambiarán a "Generated"

## Notas

- El campo `verification_code` NO es editable (se genera automáticamente)
- No se puede cambiar `student` o `event` después de crear (evita inconsistencias)
- El `status` default es 'pending' (se cambia mediante acciones batch o método `generate()`)

---

**Estado:** ✅ Corregido
**Fecha:** 29/03/2026
