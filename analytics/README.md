# Módulo de Analítica CRISP-DM — CertyPro

Predicción de **asistencia a eventos de capacitación** aplicando la metodología
**CRISP-DM** sobre los datos de CertyPro, con **consumo de una API pública gratuita**
(Nager.Date, feriados) y usando **100 % software libre**.

> 📄 El informe metodológico completo (las 6 fases) está en **`INFORME_CRISP_DM.md`**.

---

## 🎯 Qué hace

Entrena un modelo que, para cada inscripción, estima la **probabilidad de que el
participante asista**, para enviar recordatorios dirigidos y optimizar la logística.

---

## 🧩 Estructura

```
analytics/
├── crispdm/                 # Paquete reproducible (las 6 fases)
│   ├── config.py            # semilla, rutas, variables
│   ├── data_source.py       # datos reales (ORM) o sintéticos deterministas
│   ├── holidays_api.py      # CONSUMO de API externa (Nager.Date)
│   ├── features.py          # preparación / ingeniería de variables
│   ├── model.py             # entrenamiento, evaluación, guardado
│   └── pipeline.py          # orquesta las 6 fases + gráficos
├── management/commands/
│   └── crispdm_train.py     # `python manage.py crispdm_train`
├── views.py / urls.py       # endpoints REST (fase Despliegue)
├── run_crispdm.py           # runner STANDALONE (sin Django)
├── requirements-analytics.txt
├── INFORME_CRISP_DM.md
└── outputs/                 # (generado) gráficos + métricas
    models/                  # (generado) modelo .joblib
```

---

## ▶️ Replicar el análisis (modo standalone, sin base de datos)

**La forma más simple y 100 % reproducible.** Solo requiere Python 3.10+.

```bash
cd SystemCertification/analytics

# 1) Entorno e instalación
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # Linux / macOS
pip install -r requirements-analytics.txt

# 2) Ejecutar el pipeline CRISP-DM completo
python run_crispdm.py          # consulta la API de feriados
python run_crispdm.py --offline  # sin internet (usa caché / respaldo)
```

**Salidas generadas:**

- `outputs/plots/*.png` — los 6 gráficos de las fases.
- `outputs/metrics.json` — métricas de los modelos.
- `models/attendance_model.joblib` — modelo entrenado.

Gracias a la semilla fija (`RANDOM_SEED = 42`), **cualquier máquina obtiene los mismos
resultados** (ROC-AUC ≈ 0.806 en la corrida de referencia).

---

## 🌐 Ejecutar integrado con el backend Django

Desde la raíz de `SystemCertification` (requiere las dependencias del backend):

```bash
# Entrenar (usa datos reales de la BD si hay; si no, sintéticos)
python manage.py crispdm_train
python manage.py crispdm_train --synthetic --offline   # forzar reproducible

# Levantar el servidor y consumir los endpoints
python manage.py runserver
```

### Endpoints (requieren autenticación JWT)

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/api/analytics/dashboard/` | Estadísticas descriptivas |
| `GET`  | `/api/analytics/model-info/` | Métricas del modelo |
| `POST` | `/api/analytics/predict-attendance/` | Predicción de asistencia |

Ejemplo con `curl`:

```bash
curl -X POST http://localhost:8000/api/analytics/predict-attendance/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"duration_hours":8,"lead_time_days":20,"invitation_accepted":1,"is_public":1,"category":"Tecnologia"}'
```

---

## ✅ Cumplimiento de los requisitos

1. **Sistema libre** — Django, PostgreSQL, pandas, scikit-learn, Matplotlib, React (todas libres). Sin servicios de pago.
2. **Consumo de API's** — API pública Nager.Date (feriados), sin API key.
3. **Metodología CRISP-DM** — 6 fases implementadas (ver `INFORME_CRISP_DM.md`).
4. **Presentación + replicabilidad** — un comando reproduce todo con semilla fija.

---

## 🔁 Reproducibilidad — notas

- `RANDOM_SEED = 42` gobierna la generación de datos **y** el modelado.
- El consumo de API cachea en `outputs/holidays_cache.json`; `--offline` evita la red.
- Para analizar **datos reales**, basta con tener la base de datos poblada y correr
  `python manage.py crispdm_train` (sin `--synthetic`).
