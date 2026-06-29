# Instalación del Frontend

## Requisitos del Entorno

- Node.js 18+ (recomendado 20 LTS)
- npm 9+

## Instalación de Dependencias

```bash
cd certyfront
npm install
```

## Variables de Entorno

El frontend utiliza `VITE_API_URL` como variable de entorno para apuntar a la API de Django.

### Desarrollo (`.env`)

```env
VITE_API_URL=http://localhost:8000
```

### Producción (`.env.production`)

```env
VITE_API_URL=https://api.certypro.app
```

!!! hint "Proxy de Desarrollo"
    En `vite.config.ts` está configurado un proxy que redirige `/api` y `/media` a `http://localhost:8000`, por lo que en desarrollo no es necesario definir `VITE_API_URL` explícitamente a menos que la API esté en otro puerto.

## Ejecutar en Desarrollo

```bash
npm run dev
```

El servidor de desarrollo estará disponible en `http://localhost:5173`.

## Compilar para Producción

```bash
npm run build
```

Los archivos compilados se generan en el directorio `dist/`.

## Preview de Producción

```bash
npm run preview
```

## Ejecutar Pruebas

```bash
# Pruebas unitarias con Vitest
npm test

# Pruebas con cobertura
npm run test:coverage

# Pruebas E2E con Playwright (requiere servidor backend corriendo)
npx playwright test
```

!!! warning "Pruebas E2E"
    Las pruebas de Playwright requieren que el backend de Django esté corriendo en `http://localhost:8000` y que exista un usuario administrador con las credenciales `admin@certypro.com` / `admin123`.

## Abrir Interfaz Gráfica de Playwright

```bash
npx playwright test --ui
```
