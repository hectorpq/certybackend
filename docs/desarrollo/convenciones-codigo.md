# Convenciones de Código

## Backend (Python)

- **Estilo:** PEP 8 — verificado con Flake8 y Ruff
- **Tipos:** Type hints en funciones públicas
- **Formatos:** Black (default config)
- **Imports:** isort (agrupados: stdlib → django → terceros → locales)
- **Nombres:**
    - `snake_case` para variables, funciones, métodos
    - `PascalCase` para clases
    - `UPPER_CASE` para constantes
    - `_privado` para métodos internos con guión bajo

## Frontend (TypeScript/React)

- **Estilo:** ESLint + Prettier (configuración estándar)
- **Tipos:** TypeScript strict mode; evitar `any`
- **Nombres:**
    - `camelCase` para variables, funciones
    - `PascalCase` para componentes, interfaces, tipos
    - `kebab-case` para archivos
- **Componentes:** Funcionales con hooks (no clases)
- **Estado del servidor:** TanStack Query para datos de API (no Redux)
- **Estilos:** TailwindCSS (no CSS modules ni styled-components)

## Commits

Formato: `tipo(alcance): mensaje`

```
feat(api): agregar endpoint de verificación pública
fix(events): corregir cálculo de duración del evento
docs(api): documentar endpoint de login
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Documentación

- Docstrings en inglés para módulos y clases públicas
- Comentarios en español para lógica de negocio compleja
- Documentación de API via drf-spectacular (OpenAPI)
- MkDocs para documentación del proyecto
