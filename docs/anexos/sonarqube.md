# Reportes de SonarQube

## Configuración

- **URL**: `http://localhost:9000`
- **Proyecto**: `certy-backend`
- **Token**: Configurado en variables de entorno (`SONAR_TOKEN`)
- **Análisis**: Ejecutado vía `gradle sonarqube` en pipeline CI

## Métricas monitoreadas

| Métrica | Objetivo | Estado actual |
|---------|:--------:|:-------------:|
| Reliability (Bugs) | A | - |
| Security (Vulnerabilities) | A | - |
| Maintainability (Code Smells) | A | - |
| Coverage | ≥ 80 % | - |
| Duplications | ≤ 3 % | - |
| Security Hotspots | 0 | - |

## Reglas personalizadas

- Cobertura mínima en código nuevo: 80 %
- Complejidad cognitiva máxima por función: 15
- Líneas por archivo: máximo 400
- Duplicación máxima permitida: 3 %

## Gate de Calidad

El Quality Gate se compone de:

1. **Cobertura general** ≥ 80 %
2. **Cobertura en código nuevo** ≥ 80 %
3. **Bugs** = 0 en código nuevo
4. **Vulnerabilities** = 0 en código nuevo
5. **Code Smells** < 5 % en código nuevo
6. **Duplications** < 3 % en código nuevo

## Historial de Análisis

| Fecha | Bugs | Vulnerabilities | Code Smells | Coverage | Duplications |
|------|:---:|:--------------:|:-----------:|:--------:|:-----------:|
| - | - | - | - | - | - |

## Mejoras recomendadas

> Este documento debe actualizarse tras cada ejecución de SonarQube en el pipeline.
