# Procedimientos de Respaldo

## Base de Datos (PostgreSQL)

```bash
# Respaldo completo
pg_dump -h localhost -U postgres -d certificados_db > backup_$(date +%Y%m%d).sql

# Respaldo comprimido
pg_dump -h localhost -U postgres -d certificados_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Respaldo de sólo datos (sin schema)
pg_dump -h localhost -U postgres -d certificados_db --data-only > backup_data_$(date +%Y%m%d).sql
```

## Archivos Multimedia

```bash
# Respaldar archivos subidos (imágenes de plantillas, firmas)
tar -czf media_backup_$(date +%Y%m%d).tar.gz /path/to/media/

# Respaldar archivos estáticos
tar -czf static_backup_$(date +%Y%m%d).tar.gz /path/to/static/
```

## Docker (volúmenes)

```bash
# Respaldo de volúmenes Docker
docker run --rm -v db_data:/data -v $(pwd):/backup alpine tar czf /backup/db_data_$(date +%Y%m%d).tar.gz -C /data .
```

## Frecuencia Recomendada

| Recurso | Frecuencia | Retención |
|---------|------------|-----------|
| Base de datos | Diaria | 30 días |
| Archivos multimedia | Semanal | 90 días |
| Configuración | Por cambio | Indefinido |
| Volúmenes Docker | Semanal | 30 días |

## Automatización

Usar `cron` para automatizar respaldos:

```cron
# Diario a las 2:00 AM
0 2 * * * /usr/local/bin/backup_db.sh

# Semanal los domingos a las 3:00 AM
0 3 * * 0 /usr/local/bin/backup_media.sh
```
