"""
Modelado y evaluacion (CRISP-DM fases 4 y 5).

Entrena y compara dos modelos de clasificacion binaria para predecir la
asistencia:
    - Regresion Logistica (modelo lineal interpretable, baseline).
    - Random Forest (modelo no lineal, suele dar mejor desempeno).

Ambos se envuelven en un Pipeline de sklearn con preprocesamiento
(escalado numerico + one-hot de categoricas) para evitar fuga entre train/test
y garantizar que el mismo preprocesamiento se aplique en produccion.
"""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import CATEGORICAL_FEATURES, MODEL_PATH, NUMERIC_FEATURES, RANDOM_SEED, ensure_dirs


def _build_preprocessor() -> ColumnTransformer:
    # Las binarias ya son 0/1: se dejan pasar sin transformar.
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",  # binarias
    )


def _build_models() -> dict[str, Pipeline]:
    pre = _build_preprocessor()
    return {
        "logistic_regression": Pipeline(
            [("pre", pre), ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED))]
        ),
        "random_forest": Pipeline(
            [
                ("pre", _build_preprocessor()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=12,
                        min_samples_leaf=5,
                        random_state=RANDOM_SEED,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def _metrics(y_true, y_pred, y_proba) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_proba)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def train_and_evaluate(X: pd.DataFrame, y: pd.Series) -> dict:
    """
    Entrena ambos modelos, los evalua en un holdout y por validacion cruzada,
    selecciona el mejor por ROC-AUC y lo persiste en disco.

    Devuelve un diccionario con metricas, modelo ganador y datos para plots.
    """
    ensure_dirs()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y)

    results = {}
    fitted: dict[str, Pipeline] = {}
    for name, pipe in _build_models().items():
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)[:, 1]
        cv = cross_val_score(pipe, X, y, cv=5, scoring="roc_auc")
        results[name] = {
            **_metrics(y_test, y_pred, y_proba),
            "cv_roc_auc_mean": round(float(cv.mean()), 4),
            "cv_roc_auc_std": round(float(cv.std()), 4),
        }
        fitted[name] = pipe

    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    best_model = fitted[best_name]

    # Curva ROC del mejor modelo (para graficar).
    y_proba_best = best_model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_proba_best)

    # Importancia de variables (si el modelo ganador la expone).
    importances = _feature_importances(best_model)

    joblib.dump(best_model, MODEL_PATH)

    return {
        "results": results,
        "best_model_name": best_name,
        "best_model": best_model,
        "model_path": str(MODEL_PATH),
        "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "feature_importances": importances,
        "test_target_rate": round(float(y_test.mean()), 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }


def _feature_importances(model: Pipeline) -> list[dict] | None:
    """Extrae importancias de variables tras el preprocesamiento (one-hot incluido)."""
    clf = model.named_steps["clf"]
    pre = model.named_steps["pre"]
    try:
        names = pre.get_feature_names_out()
    except Exception:  # noqa: BLE001
        return None

    if hasattr(clf, "feature_importances_"):
        vals = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        vals = np.abs(clf.coef_[0])
    else:
        return None

    pairs = sorted(zip(names, vals), key=lambda p: p[1], reverse=True)
    return [{"feature": str(n), "importance": round(float(v), 4)} for n, v in pairs[:15]]


def load_model() -> Pipeline:
    """Carga el modelo entrenado (para la fase de Despliegue)."""
    return joblib.load(MODEL_PATH)
