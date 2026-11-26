---
title: Sistema Libre
---

# :fontawesome-solid-lock-open: Sistema Libre

!!! info "Requisito 1"
    CertyPro está construido **íntegramente con software libre y de código abierto**.
    No se utiliza ninguna librería, framework, base de datos ni servicio que requiera
    licencia de pago. Cualquier persona puede instalar, modificar y redistribuir el sistema.

---

## ¿Qué es software libre?

El **software libre** (Free/Open Source Software — FOSS) cumple cuatro libertades esenciales:

| Libertad | Descripción |
|:---:|---|
| **0** | Usar el programa con cualquier propósito |
| **1** | Estudiar y modificar el código fuente |
| **2** | Distribuir copias del programa |
| **3** | Distribuir versiones modificadas |

CertyPro respeta estas libertades en todos sus componentes.

---

## Inventario de tecnologías libres

### Backend

| Tecnología | Licencia | Versión |
|---|---|---|
| Python | PSF License (libre) | 3.10 |
| Django | BSD 3-Clause | 5.2.12 |
| Django REST Framework | BSD | 3.14 |
| djangorestframework-simplejwt | MIT | 5.3 |
| PostgreSQL | PostgreSQL License (libre) | 15 |
| Redis | BSD 3-Clause | 7 |
| Celery | BSD | 5 |
| ReportLab | BSD | 4.0.7 |
| pandas | BSD | 2.1.3 |
| Whitenoise | MIT | — |
| django-simple-history | LGPL | 3.7 |
| drf-spectacular | BSD | — |

### Analítica CRISP-DM

| Tecnología | Licencia | Versión |
|---|---|---|
| scikit-learn | BSD 3-Clause | 1.4.2 |
| NumPy | BSD | 1.26.4 |
| Matplotlib | PSF-based | 3.8.4 |
| joblib | BSD | 1.4.0 |
| requests | Apache 2.0 | 2.32.3 |

### Frontend

| Tecnología | Licencia | Versión |
|---|---|---|
| React | MIT | 18 |
| Vite | MIT | 5 |
| TypeScript | Apache 2.0 | 5 |
| TailwindCSS | MIT | 3 |
| Playwright (tests e2e) | Apache 2.0 | — |

### Infraestructura y herramientas

| Tecnología | Licencia | Propósito |
|---|---|---|
| Docker | Apache 2.0 | Contenedorización |
| Docker Compose | Apache 2.0 | Orquestación local |
| GitHub Actions | MIT (runners) | CI/CD gratuito |
| GitHub Pages | Gratuito | Hosting de documentación |
| Material for MkDocs | MIT | Este sitio de documentación |
| MkDocs | BSD | Generador de sitio estático |

---

## Hosting gratuito

!!! tip "Sin costo de infraestructura"
    Todo el sistema puede desplegarse **sin pagar nada**:

=== "Backend"
    - **[Render](https://render.com)** — plan gratuito para Django + PostgreSQL
    - **[Railway](https://railway.app)** — $5/mes de crédito gratuito
    - **[Fly.io](https://fly.io)** — tier gratuito para aplicaciones pequeñas

=== "Frontend"
    - **[Vercel](https://vercel.com)** — plan gratuito, ya configurado (`vercel.json`)
    - **[Netlify](https://netlify.com)** — plan gratuito con deploy automático
    - **GitHub Pages** — para sites estáticos

=== "Base de datos"
    - **[Supabase](https://supabase.com)** — PostgreSQL gratuito (500 MB)
    - **[Neon](https://neon.tech)** — PostgreSQL serverless gratuito

=== "Documentación"
    - **GitHub Pages** — este sitio, 100 % gratuito
    - Generado automáticamente al hacer `git push`

---

## Verificación de licencias

```bash
# Ver todas las licencias del proyecto backend
cd SystemCertification
pip-licenses --format=table --order=license 2>/dev/null
```

Ninguna de las dependencias tiene una licencia restrictiva o comercial.

!!! success "Conclusión"
    CertyPro cumple plenamente con el requisito de **sistema libre**: cada componente —
    desde el lenguaje de programación hasta el sistema de gestión de base de datos, el
    framework web, las librerías de análisis de datos y el hosting — es software de
    código abierto con licencia permisiva (MIT, BSD, Apache 2.0, PSF).
