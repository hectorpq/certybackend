---
title: "Fase 5 — Evaluación"
---

# :fontawesome-solid-chart-bar: Fase 5 — Evaluación

!!! abstract "Objetivo de esta fase"
    Comparar los modelos entrenados, verificar si se alcanzan los criterios de éxito
    definidos en la Fase 1, interpretar los resultados en términos de negocio y decidir
    si el modelo está listo para ser desplegado.

---

## 5.1 Comparación de modelos

| Modelo | ROC-AUC | F1 | Accuracy | Precision | Recall | CV ROC-AUC |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Regresión Logística** ✅ | **0.806** | **0.825** | **0.767** | 0.783 | 0.872 | **0.764** |
| Random Forest | 0.796 | 0.820 | 0.745 | — | — | 0.710 |

!!! success "Modelo ganador: Regresión Logística"
    Supera al Random Forest en las métricas clave **y** es más interpretable,
    lo cual es crucial para explicar las predicciones a los coordinadores de eventos.

---

## 5.2 Verificación del criterio de éxito

| Criterio | Umbral | Resultado | Estado |
|---|:---:|:---:|:---:|
| **CV ROC-AUC ≥ 0.75** | 0.75 | **0.764** | ✅ ALCANZADO |
| **F1-Score ≥ 0.70** | 0.70 | **0.825** | ✅ ALCANZADO |
| **Recall (ausentes) ≥ 0.65** | 0.65 | **0.872** | ✅ ALCANZADO |

!!! success "Todos los criterios alcanzados"
    El modelo cumple los estándares definidos en la Fase 1 y está listo para su despliegue.

---

## 5.3 Importancia de variables

Las 10 variables más influyentes en el modelo de Regresión Logística:

| Rango | Variable | Importancia relativa | Interpretación |
|:---:|---|:---:|---|
| 1 | `invitation_accepted` | ████████ alta | Aceptar la invitación = mayor compromiso |
| 2 | `near_holiday` (**API**) | ███████ alta | Feriado cercano = menor asistencia |
| 3 | `is_public` | █████ media | Eventos públicos = mayor asistencia |
| 4 | `lead_time_days` | █████ media | Inscripción anticipada = mayor compromiso |
| 5 | `duration_hours` | ████ media | Eventos largos = menor asistencia |
| 6 | `participant_prior_rate` | ███ media | Historial previo predice comportamiento futuro |
| 7 | `was_invited` | ███ media | Recibir invitación formal aumenta asistencia |
| 8 | `event_month` | ██ baja | Efecto estacional |
| 9 | `event_dow` | ██ baja | Día de la semana tiene efecto menor |
| 10 | `category_Idiomas` | █ baja | Idiomas tiene menor tasa que otras categorías |

!!! note "Interpretación de negocio"
    Las variables de mayor peso tienen sentido intuitivo para los coordinadores:
    un participante que **aceptó la invitación** e **inscribió con días de anticipación**,
    y cuyo evento **no cae cerca de un feriado**, tiene una alta probabilidad de asistir.

---

## 5.4 Matriz de confusión

Sobre el conjunto de prueba (459 inscripciones):

|  | **Pred: No asistió** | **Pred: Asistió** |
|---|:---:|:---:|
| **Real: No asistió** | TN: ~148 | FP: ~69 |
| **Real: Asistió** | FN: ~38 | TP: ~204 |

**Lectura de negocio:**
- **204 verdaderos positivos:** participantes que se predijo que asistirían y sí asistieron → no se envía recordatorio innecesario
- **148 verdaderos negativos:** participantes que se predijo que faltarían y sí faltaron → recordatorio enviado correctamente
- **38 falsos negativos:** ausentes que el modelo no detectó → área de mejora
- **69 falsos positivos:** recordatorios enviados a quienes sí habrían asistido → bajo costo (solo un email de más)

---

## 5.5 Curva ROC

La curva ROC del modelo ganador (Regresión Logística):

```
AUC = 0.806
     ┌──────────────────────────┐
1.0  │       ╭────────────────  │
     │     ╭─╯                  │
0.8  │   ╭─╯                    │
     │  ╭╯                      │
0.6  │ ╭╯                       │
     │╭╯                        │
0.4  ││  Modelo               ──│
     │╰─────── aleatoria ───────│
0.0  └──────────────────────────┘
     0.0  0.2  0.4  0.6  0.8  1.0
           Tasa de Falsos Positivos
```

*(Gráfico completo en `analytics/outputs/plots/06_roc_curve.png`)*

---

## 5.6 Validación cruzada

```
Fold 1: ROC-AUC = 0.771
Fold 2: ROC-AUC = 0.758
Fold 3: ROC-AUC = 0.769
Fold 4: ROC-AUC = 0.753
Fold 5: ROC-AUC = 0.771
─────────────────────────
Media:  0.764  ✅ ≥ 0.75
Desv.:  ±0.008 (muy estable)
```

La baja desviación estándar confirma que el modelo **generaliza bien** y no está
sobreajustado a un subconjunto de los datos.

---

## 5.7 Decisión: ¿Desplegar?

| Pregunta | Respuesta |
|---|---|
| ¿El modelo supera el criterio de éxito? | ✅ Sí (CV-AUC = 0.764 > 0.75) |
| ¿Los resultados tienen sentido de negocio? | ✅ Sí (variables coherentes) |
| ¿Es lo suficientemente interpretable? | ✅ Sí (Regresión Logística = coeficientes directos) |
| ¿Es reproducible con nuevos datos? | ✅ Sí (pipeline serializado con joblib) |

!!! success "Decisión: Desplegar"
    El modelo pasa a la **Fase 6 de Despliegue**, exponiéndose como endpoint REST
    en la API de CertyPro.

---

## 5.8 Limitaciones y mejoras futuras

!!! warning "Limitaciones del modelo actual"
    - Entrenado sobre datos **sintéticos**: con datos reales de producción, las métricas
      podrían variar.
    - No incorpora **texto** (nombre del evento, descripción) como feature.
    - El historial del participante es limitado en las primeras inscripciones (cold start).

**Mejoras propuestas (iteración siguiente):**

1. Reentrenar con datos reales al tener ≥ 500 inscripciones en la BD
2. Incorporar el canal de inscripción (invitación vs. auto-inscripción)
3. Añadir la **distancia geográfica** del participante al evento (si se tiene ubicación)
4. Evaluar modelos de Gradient Boosting (XGBoost, LightGBM)
