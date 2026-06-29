# Análisis de Código con SonarQube

La calidad del código, tanto del **frontend** como del **backend**, se monitorea continuamente utilizando SonarQube. Esta herramienta nos ayuda a detectar bugs, vulnerabilidades, "code smells" y a medir la cobertura de las pruebas unitarias.

## Problema Original y Solución

Inicialmente, el pipeline de CI/CD (Jenkins) para el frontend fallaba porque SonarQube reportaba una cobertura de pruebas incorrectamente baja (ej: 12.6%), cuando las pruebas locales indicaban un valor mucho mayor.

### Causa

La causa principal era una mala configuración que impedía que SonarQube encontrara el reporte de cobertura (`lcov.info`) generado por Vitest.

### Solución Implementada

1.  **`vite.config.ts`**: Se configuró Vitest para que genere múltiples formatos de reporte, incluyendo `lcov`, que es el formato que SonarQube necesita para interpretar los resultados de cobertura.
    ```typescript
    test: {
      coverage: {
        reporter: ['text', 'json', 'html', 'lcov'],
      }
    }
    ```

2.  **`Jenkinsfile`**: Se actualizó el *stage* del pipeline para pasar explícitamente la ruta del reporte LCOV al scanner de SonarQube.
    ```groovy
    // ... dentro del stage de SonarQube
    sh "sonar-scanner -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info"
    ```

3.  **`sonar-project.properties`**: Se optimizó este archivo para incluir exclusiones de cobertura (ej: archivos de configuración, mocks, `main.tsx`) y definir correctamente los sufijos de los archivos a analizar (`.ts`, `.tsx`).

## Métricas Clave en SonarQube

- **Coverage**: Porcentaje del código que está cubierto por pruebas unitarias. Después de la corrección, esta métrica muestra un valor realista (ej: > 22%).
- **Bugs y Vulnerabilidades**: Problemas en el código que podrían llevar a un comportamiento incorrecto o a brechas de seguridad.
- **Code Smells**: Partes del código que, aunque funcionales, son difíciles de mantener.
- **Duplications**: Bloques de código repetidos que deberían ser refactorizados.
- **Quality Gate**: Un conjunto de condiciones (ej: "la cobertura no debe ser menor al 80%") que el código debe cumplir para ser considerado "apto para producción". El pipeline de CI/CD puede ser configurado para fallar si el Quality Gate no se aprueba.

## Ejecución del Análisis

El análisis de SonarQube se ejecuta automáticamente en el pipeline de CI/CD después de que las pruebas unitarias pasan.

Para ejecutar un análisis localmente en el frontend (útil para debugging):

1.  Genera el reporte de cobertura: `npm run test:coverage`
2.  Ejecuta el scanner con el script proporcionado:
    ```powershell
    $env:SONAR_TOKEN = 'tu-token-de-sonarqube'
    .\run-sonarqube-analysis.ps1
    ```