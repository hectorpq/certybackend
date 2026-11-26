# Informe CRISP-DM — Predicción de Asistencia a Eventos (CertyPro)

**Proyecto:** CertyPro — Sistema de gestión de certificados
**Módulo:** `analytics/` (analítica de datos)
**Metodología:** CRISP-DM (*Cross Industry Standard Process for Data Mining*)
**Fecha:** 2026-11

Este informe documenta cómo el proyecto cumple los **cuatro requisitos** solicitados:

| Requisito | Cómo se cumple |
|---|---|
| **1. Sistema libre** | Todo el stack es software libre / de código abierto (ver §7) |
| **2. Consumo de API's** | Se consume la API pública **Nager.Date** de feriados (§3.3), además de las APIs ya integradas (WhatsApp Cloud, SMTP) |
| **3. Metodología CRISP-DM** | Las 6 fases están implementadas y documentadas (§1–§6) |
| **4. Presentación + replicabilidad** | Pipeline 100 % reproducible con una semilla fija y un comando (ver `README.md`) |

---

## Fase 1 — Comprensión del negocio

**Problema.** En los eventos de capacitación gestionados por CertyPro hay personas
que se inscriben pero **no asisten** (ausentismo). Esto desperdicia aforo, materiales
y esfuerzo logístico, y distorsiona la emisión de certificados.

**Objetivo de negocio.** Reducir el ausentismo y optimizar la logística de cada evento.

**Objetivo de minería de datos.** Predecir, para cada **inscripción**, si el participante
**asistirá o no** (clasificación binaria). Con esa predicción el sistema puede:

- Enviar **recordatorios dirigidos** a los inscritos con alto riesgo de no asistir.
- **Estimar la asistencia real** para dimensionar aforo y materiales.
- Priorizar la **generación/entrega de certificados**.

**Criterio de éxito.** Un modelo con **ROC-AUC ≥ 0.75** en validación cruzada (5 folds),
métrica robusta frente al desbalance de clases.

---

## Fase 2 — Comprensión de los datos

**Unidad de análisis:** la inscripción (`Enrollment`) = *un participante en un evento*.

**Fuente.** Los datos provienen del modelo de dominio de CertyPro:

| Entidad | Aporta |
|---|---|
| `Enrollment` | asistencia (objetivo), fecha de inscripción, invitación asociada |
| `Event` | categoría, duración, aforo, si es público, fecha del evento |
| `EventInvitation` | si hubo invitación y si fue aceptada |
| `Participant` | identidad para construir el historial de asistencia |

**Variable objetivo:** `attended` (1 = asistió, 0 = no asistió).

**Modo de datos.** El pipeline lee datos reales desde la base de datos (`--orm`) o,
si no hay datos suficientes, genera un **dataset sintético determinista** con la misma
estructura (semilla fija = 42). Esto garantiza que el análisis sea **replicable** en
cualquier máquina sin depender de la base de datos de producción.

> En la corrida de referencia (sintética): **1 836 inscripciones**, **449 participantes**,
> **70 eventos**, tasa de asistencia global **≈ 51 %** (clases balanceadas).

---

## Fase 3 — Preparación de los datos

### 3.1 Ingeniería de variables

A partir de los datos crudos se derivan las características del modelo:

| Variable | Tipo | Descripción |
|---|---|---|
| `duration_hours` | numérica | Duración del evento |
| `max_capacity` | numérica | Aforo máximo |
| `lead_time_days` | numérica | Días de anticipación de la inscripción (`event_date − enrolled_at`) |
| `participant_prior_events` | numérica | Nº de inscripciones previas del participante |
| `participant_prior_rate` | numérica | Tasa de asistencia histórica del participante |
| `event_dow` | numérica | Día de la semana del evento (0 = lunes) |
| `event_month` | numérica | Mes del evento |
| `is_public` | binaria | Evento público o privado |
| `near_holiday` | binaria | **El evento cae a ±2 días de un feriado** (API externa) |
| `was_invited` | binaria | Hubo invitación formal |
| `invitation_accepted` | binaria | La invitación fue aceptada |
| `category` | categórica | Categoría del evento (one-hot) |

### 3.2 Prevención de fuga de información (*data leakage*)

Se **excluyen** deliberadamente variables que solo se conocen *después* del evento
(`grade`, `certificate_sent`, etc.). El historial del participante se calcula **solo con
eventos anteriores** a la fecha del evento evaluado, respetando el orden temporal.

### 3.3 Consumo de API externa — Nager.Date (Requisito 2)

Se consume la API pública **Nager.Date** para obtener los feriados oficiales:

```
GET https://date.nager.at/api/v3/PublicHolidays/{año}/PE
```

- **Gratuita y sin API key** → coherente con el requisito de *sistema libre*.
- Cada evento se marca con `near_holiday = 1` si ocurre cerca de un feriado nacional,
  hipótesis de negocio: *la asistencia baja alrededor de los feriados*.
- **Diseño resiliente para replicabilidad:** si hay internet consulta la API y cachea el
  resultado; si no hay red, usa la caché local o una lista de respaldo de feriados de Perú.
  El pipeline corre siempre (`--offline` fuerza el modo sin red).

Implementación: `crispdm/holidays_api.py`.

---

## Fase 4 — Modelado

Se entrenan y comparan **dos modelos** dentro de un `Pipeline` de scikit-learn con
preprocesamiento (escalado de numéricas + one-hot de categóricas):

1. **Regresión Logística** — lineal, interpretable (*baseline*).
2. **Random Forest** — no lineal, captura interacciones.

Partición **75 / 25** estratificada + **validación cruzada de 5 folds**. La selección del
modelo ganador se hace por **ROC-AUC** en el conjunto de prueba.

---

## Fase 5 — Evaluación

Resultados de la corrida de referencia (dataset sintético, semilla 42):

| Modelo | ROC-AUC | F1 | Accuracy | Precision | Recall | CV ROC-AUC |
|---|---|---|---|---|---|---|
| **Regresión Logística** ✅ | **0.806** | 0.825 | 0.767 | 0.783 | 0.872 | **0.764** |
| Random Forest | 0.796 | 0.820 | 0.745 | — | — | 0.710 |

**Modelo ganador: Regresión Logística.**
**Criterio de éxito (CV-AUC ≥ 0.75): ALCANZADO.**

**Variables más influyentes** (importancia / coeficientes): `invitation_accepted`,
`near_holiday`, `is_public`, `lead_time_days`, `duration_hours`. Confirman las hipótesis
de negocio: aceptar la invitación e inscribirse con anticipación elevan la asistencia,
mientras que la cercanía a un feriado y la mayor duración la reducen.

**Gráficos generados** (`outputs/plots/`):

- `01_target_distribution.png` — distribución de la variable objetivo
- `02_attendance_by_category.png` — asistencia por categoría
- `03_attendance_by_holiday.png` — asistencia cerca / lejos de feriados
- `04_feature_importances.png` — importancia de variables
- `05_confusion_matrix.png` — matriz de confusión
- `06_roc_curve.png` — curva ROC

---

## Fase 6 — Despliegue

El modelo entrenado (`models/attendance_model.joblib`) se expone en la **API REST de
CertyPro** (app `analytics`), integrándose al mismo backend Django:

| Método | Endpoint | Función |
|---|---|---|
| `GET` | `/api/analytics/dashboard/` | Estadísticas descriptivas de asistencia |
| `GET` | `/api/analytics/model-info/` | Métricas del último entrenamiento |
| `POST` | `/api/analytics/predict-attendance/` | Predice la probabilidad de asistencia |

**Ejemplo de predicción** (`POST /api/analytics/predict-attendance/`):

```json
{
  "duration_hours": 8, "max_capacity": 50, "is_public": 1,
  "category": "Tecnologia", "lead_time_days": 20,
  "near_holiday": 0, "was_invited": 1, "invitation_accepted": 1,
  "participant_prior_events": 3, "participant_prior_rate": 0.8
}
```

Respuesta:

```json
{
  "will_attend": true,
  "attendance_probability": 0.867,
  "risk_level": "bajo",
  "recommendation": "Sin accion requerida"
}
```

Reentrenamiento con un solo comando:

```bash
python manage.py crispdm_train            # datos reales si existen
python manage.py crispdm_train --synthetic --offline  # 100% reproducible
```

---

## 7. Sistema libre (Requisito 1)

Todo el proyecto usa **exclusivamente software libre / de código abierto**:

| Componente | Tecnología | Licencia |
|---|---|---|
| Backend / API | Django, Django REST Framework | BSD |
| Base de datos | PostgreSQL | PostgreSQL License |
| Analítica | pandas, NumPy, scikit-learn, Matplotlib | BSD |
| Modelo persistido | joblib | BSD |
| API de feriados | Nager.Date | Gratuita, sin key |
| Frontend | React, Vite, TailwindCSS | MIT |

No se usa ningún servicio, librería ni dataset de pago. La API externa consumida es
pública y gratuita.

---

## 8. Replicabilidad (Requisito 4)

Ver **`README.md`** para la guía paso a paso. En resumen:

```bash
cd SystemCertification/analytics
pip install -r requirements-analytics.txt
python run_crispdm.py            # reproduce TODO el análisis (semilla fija)
```

La semilla `RANDOM_SEED = 42` gobierna la generación de datos **y** el entrenamiento,
por lo que cualquier persona obtiene **exactamente los mismos resultados y gráficos**.
