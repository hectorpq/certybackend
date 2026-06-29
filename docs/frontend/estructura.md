# Estructura General del Frontend

El frontend de CertySys está construido con React, Vite y TypeScript, siguiendo una arquitectura modular y escalable.

## Directorios Principales

```
certyfront/
├── public/           # Archivos estáticos
├── src/
│   ├── assets/       # Imágenes, fuentes, etc.
│   ├── components/   # Componentes reutilizables (UI y de lógica)
│   │   └── ui/       # Componentes de UI puros (Button, Input, Card, etc.)
│   ├── config/       # Configuración de la aplicación
│   ├── hooks/        # Hooks personalizados (ej: useAuth, useStudents)
│   ├── layouts/      # Estructuras de página (DashboardLayout, AuthLayout)
│   ├── pages/        # Componentes de página (una por ruta)
│   ├── services/     # Lógica de comunicación con la API (api.ts)
│   ├── styles/       # Estilos globales (index.css con Tailwind)
│   ├── test/         # Archivos de pruebas unitarias e integración
│   └── utils/        # Funciones de utilidad
├── .env              # Variables de entorno
├── index.html        # Punto de entrada HTML
├── package.json      # Dependencias y scripts
└── vite.config.ts    # Configuración de Vite y Vitest
```

## Flujo de Datos

1.  **Pages**: Renderizan la vista principal de una ruta.
2.  **Hooks**: Gestionan el estado y la lógica de negocio (ej: `useAuth` para el estado de autenticación, `useStudents` para obtener datos de participantes).
3.  **Services**: `api.ts` (una instancia de Axios) centraliza todas las peticiones al backend.
4.  **Components**: Reciben datos y funciones a través de props y renderizan la UI.