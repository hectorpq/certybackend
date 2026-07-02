# Procedimientos de Restauración

## Base de Datos

```bash
# Restaurar desde SQL
psql -h localhost -U postgres -d certificados_db < backup_20250101.sql

# Restaurar desde comprimido
gunzip -c backup_20250101.sql.gz | psql -h localhost -U postgres -d certificados_db

# Crear BD vacía si es necesario
createdb -h localhost -U postgres certificados_db
```

## Archivos Multimedia

```bash
# Restaurar archivos subidos
tar -xzf media_backup_20250101.tar.gz -C /path/to/
```

## Docker (volúmenes)

```bash
# Restaurar volumen Docker
docker run --rm -v db_data:/data -v $(pwd):/backup alpine sh -c "tar xzf /backup/db_data_20250101.tar.gz -C /data"
```

## Procedimiento Completo de Recuperación

1. Detener servicios: `docker-compose down`
2. Restaurar base de datos desde el respaldo más reciente
3. Restaurar archivos multimedia
4. Verificar integridad: `python manage.py check`
5. Iniciar servicios: `docker-compose up -d`
6. Verificar funcionalidad: login, listar certificados, generar PDF

## Plan de Recuperación ante Desastres

| Escenario | RTO | RPO | Acción |
|-----------|-----|-----|--------|
| Falla de BD | 2h | 24h | Restaurar desde respaldo diario |
| Falla de servidor | 4h | 24h | Aprovisionar nuevo servidor + restaurar respaldo |
| Error humano (datos corruptos) | 1h | 1h | Restaurar punto anterior desde respaldo |
| Desastre total (data center) | 24h | 24h | Restaurar en infraestructura alternativa |
