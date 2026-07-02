# Releases

## Versionado Semántico

**Formato**: `MAJOR.MINOR.PATCH`

| Componente | Cambio |
|:----------:|--------|
| MAJOR | Cambio incompatible en API |
| MINOR | Nueva funcionalidad compatible |
| PATCH | Corrección de bugs compatible |

## Historial de Releases

### v1.0.0 (—)

**Fecha**: —
**Estado**: Pendiente

#### Funcionalidades
- [ ] Gestión de eventos académicos
- [ ] Diseño de plantillas de certificados
- [ ] Carga masiva de participantes
- [ ] Generación de PDF con código QR
- [ ] Distribución por email (SendGrid)
- [ ] Distribución por WhatsApp (Meta API)
- [ ] Verificación pública de certificados
- [ ] Roles y permisos (admin, coordinador, participante)
- [ ] Historial de entregas y auditoría
- [ ] Documentación MkDocs completa

## Changelog

Ver [`mantenimiento/changelog.md`](../mantenimiento/changelog.md) para el detalle completo de cambios.

## Procedimiento de Release

1. Crear rama `release/<version>` desde `develop`
2. Ejecutar pruebas completas
3. Actualizar versión en `backend/certy/settings.py`
4. Generar changelog
5. Crear tag y release en GitHub
6. Merge a `main` y `develop`
7. Desplegar a producción
