# Procedimientos de Actualización

## Actualización de Dependencias

```bash
# Backend
cd certybackend
pip list --outdated
pip install --upgrade -r requirements.txt

# Frontend
cd certyfront
npm outdated
npm update
```

## Migraciones de Base de Datos

```bash
# Crear migraciones después de cambios en modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Verificar estado
python manage.py showmigrations
```

## Proceso de Release

1. Crear rama `release/vX.Y.Z` desde `develop`
2. Actualizar versión en configuración
3. Actualizar `changelog.md`
4. Ejecutar suite completa de pruebas
5. Crear tag `git tag -a vX.Y.Z`
6. Merge a `main` y `develop`
7. Desplegar en producción

## Rollback

```bash
# Revertir migración
python manage.py migrate <app_name> <numero_migracion_anterior>

# Revertir release en Git
git revert <commit_hash>
git push origin main

# Restaurar respaldo de BD si es necesario
# (ver procedimiento de restauración)
```

## Notas

- Las migraciones deben ser reversibles
- Probar actualizaciones en entorno de staging antes de producción
- Notificar a usuarios con anticipación sobre ventanas de mantenimiento
