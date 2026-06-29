# Instalación del Frontend (React + Vite)

Esta guía cubre la instalación y configuración del frontend de CertySys, desarrollado con React y Vite.

## 🔧 Stack Tecnológico

| Componente          | Detalle           |
| ------------------- | ----------------- |
| **Framework**       | React 18.2        |
| **Bundler**         | Vite              |
| **Lenguaje**        | TypeScript        |
| **Estilos**         | TailwindCSS       |
| **Routing**         | React Router DOM  |
| **Peticiones API**  | Axios             |
| **Gestión de Estado** | TanStack Query  |
| **Tests**           | Vitest, RTL, Playwright |

---

## 🚀 Instalación

### 1. Navegar al Directorio
```bash
cd certysys/certyfront
```

### 2. Instalar Dependencias
```bash
npm install
```

### 3. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz de `certyfront/` para apuntar al backend.
```env
# certyfront/.env
VITE_API_URL=http://localhost:8000
```

### 4. Ejecutar Servidor de Desarrollo
```bash
npm run dev
```
La aplicación estará disponible en `http://localhost:5173` (o el puerto que indique Vite).