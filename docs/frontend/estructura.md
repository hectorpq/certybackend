# Estructura General del Frontend

## Arquitectura

El frontend está construido con **React 18 + TypeScript + Vite 5**, con las siguientes bibliotecas principales:

- **React Router DOM v6** — Enrutamiento con protección de rutas
- **TanStack React Query v5** — Gestión de estado del servidor (caching, mutaciones)
- **Axios** — Cliente HTTP con interceptores JWT
- **React Hook Form + Zod** — Formularios con validación
- **Recharts** — Gráficos del dashboard
- **TailwindCSS 3** — Estilos utilitarios
- **Lucide React** — Iconos SVG

## Mapa de Carpetas

```
certyfront/src/
├── App.tsx                    # Router principal con rutas protegidas
├── main.tsx                   # Punto de entrada
├── index.css                  # Estilos globales + Tailwind
├── vite-env.d.ts              # Tipos de Vite
│
├── components/
│   ├── layout/
│   │   ├── Layout.tsx         # Layout principal con Sidebar + contenido
│   │   └── Sidebar.tsx        # Navegación lateral (colapsable)
│   └── ui/                    # Componentes atómicos reutilizables
│       ├── Alert.tsx, Badge.tsx, Button.tsx, Card.tsx
│       ├── FileUpload.tsx, Modal.tsx, Pagination.tsx
│       ├── SearchInput.tsx, Select.tsx, SignaturePad.tsx
│       ├── Spinner.tsx, Textarea.tsx, index.ts
│       └── PageLoader.tsx     # Loader de página completa
│
├── contexts/
│   └── ThemeContext.tsx        # Contexto de tema claro/oscuro
│
├── hooks/
│   ├── useAuth.ts             # Hook de autenticación (login, logout, sesión)
│   ├── useCertificates.ts     # CRUD + bulk de certificados
│   ├── useEvents.ts           # CRUD de eventos, inscripciones, stats
│   ├── useInstructors.ts      # CRUD de instructores
│   ├── useTemplates.ts        # CRUD de plantillas
│   └── useTheme.ts            # Hook del theme
│
├── pages/
│   ├── index.ts               # Barrel export de todas las páginas
│   ├── auth/                  # LoginPage, LoginPageWrapper, RegisterPage
│   ├── bulk/                  # BulkGeneratePage (carga masiva)
│   ├── certificates/          # CertificatesPage, CertificateDetailPage
│   ├── dashboard/             # DashboardPage (estadísticas)
│   ├── events/                # EventsPage, EventDetailPage
│   ├── instructors/           # InstructorsPage
│   ├── invitation/            # InvitationPage (pública, por token)
│   ├── participants/          # ParticipantsPage
│   └── templates/             # TemplatesPage
│
├── services/
│   ├── api.ts                 # Cliente Axios con interceptores
│   ├── authService.ts         # Servicio de autenticación (login, register, Google OAuth)
│   ├── certificateService.ts  # Servicio de certificados
│   └── instructorService.ts   # Servicio de instructores
│
├── types/
│   └── index.ts               # Interfaces TypeScript globales
│
├── utils/
│   └── errorHandling.ts       # Utilidades de manejo de errores
│
└── test/                      # Pruebas unitarias con Vitest + Testing Library
    └── setup.ts
```

## Árbol de Rutas (`App.tsx`)

- `/login` — Página de inicio de sesión (pública)
- `/register` — Registro de nuevo usuario (pública)
- `/invitation/:token` — Aceptar invitación por token (pública)
- `/dashboard` — Panel de estadísticas (protegida)
- `/participants` — Gestión de participantes (protegida)
- `/events` — Lista de eventos (protegida)
- `/events/:id` — Detalle de evento (protegida)
- `/instructors` — Gestión de instructores (protegida)
- `/certificates` — Lista de certificados (protegida)
- `/templates` — Gestión de plantillas (protegida)
- `/bulk-generate` — Generación masiva (protegida + solo admin/coordinador)

## Componentes del Layout

- **`Layout.tsx`:** Contenedor principal con flexbox. Renderiza el `Sidebar` a la izquierda y el contenido (`<Outlet />`) a la derecha. Fondo con patrón de puntos sutiles y tema adaptable.
- **`Sidebar.tsx`:** Barra lateral colapsable con degradado azul marino (modo claro) o negro profundo (modo oscuro). Muestra navegación diferenciada: admin/coordinador ven 7 opciones, participante ve solo Dashboard y Mis Certificados. Incluye avatar con iniciales, nombre de usuario, email y botón de cierre de sesión.
