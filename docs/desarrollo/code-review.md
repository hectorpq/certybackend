# Guía de Code Review

## Checklist para el Revisor

### Funcionalidad
- [ ] El código cumple con el requisito especificado
- [ ] Los casos borde están manejados (errores, nulos, vacíos)
- [ ] No hay regresiones en funcionalidad existente

### Estilo y Calidad
- [ ] Sigue las convenciones de código del proyecto
- [ ] Nombres de variables/funciones son descriptivos
- [ ] No hay código muerto, comentado o duplicado
- [ ] Los imports están ordenados

### Seguridad
- [ ] Validación de entrada de usuario (SQL injection, XSS)
- [ ] Permisos correctos en endpoints
- [ ] No hay secretos hardcodeados
- [ ] Las consultas ORM usan `select_related`/`prefetch_related` donde corresponde

### Pruebas
- [ ] Las pruebas existentes pasan
- [ ] Cobertura adecuada para el cambio
- [ ] Pruebas para casos de error

### Documentación
- [ ] Docstrings en funciones públicas nuevas
- [ ] Actualización de documentación si aplica
- [ ] Comentarios para lógica compleja

## Proceso

1. El autor asigna revisores al PR
2. Los revisores tienen 24h hábiles para revisar
3. Discutir cambios mediante comentarios en el PR
4. El autor hace los cambios solicitados
5. Aprobación → merge por el autor
