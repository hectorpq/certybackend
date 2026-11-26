"""
Orquestador del pipeline CRISP-DM de punta a punta.

Ejecuta las 6 fases en orden, imprime un resumen por consola, genera graficos
(PNG) y persiste metricas (JSON) y el modelo entrenado (joblib).

Uso standalone:
    python run_crispdm.py

Uso programatico:
    from analytics.crispdm.pipeline import run_pipeline
    report = run_pipeline(prefer_orm=True)
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")  # backend sin GUI: reproducible en servidores / CI
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .config import METRICS_PATH, PLOTS_DIR, TARGET, ensure_dirs  # noqa: E402
from .data_source import load_raw  # noqa: E402
from .features import build_feature_matrix  # noqa: E402
from .model import train_and_evaluate  # noqa: E402


def _print_header(phase: str, title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  CRISP-DM · {phase} — {title}")
    print("=" * 70)


def business_understanding() -> None:
    _print_header("Fase 1", "Comprension del negocio")
    print(
        "  Objetivo de negocio: reducir el ausentismo en eventos de capacitacion.\n"
        "  Objetivo de mineria: predecir si un participante inscrito ASISTIRA\n"
        "  (clasificacion binaria), para enviar recordatorios dirigidos y optimizar\n"
        "  logistica (aforo, materiales, certificados).\n"
        "  Metrica de exito: ROC-AUC >= 0.75 en validacion cruzada."
    )


def data_understanding(df: pd.DataFrame, source: str) -> None:
    _print_header("Fase 2", "Comprension de los datos")
    rate = df[TARGET].mean()
    print(f"  Origen de datos: {source}")
    print(f"  Inscripciones (filas): {len(df)}")
    print(f"  Participantes unicos:  {df['participant_id'].nunique()}")
    print(f"  Eventos unicos:        {df['event_id'].nunique()}")
    print(f"  Tasa de asistencia global: {rate:.1%}")
    print(f"  Categorias: {sorted(df['category'].unique().tolist())}")


def _plot_target_distribution(df: pd.DataFrame) -> None:
    counts = df[TARGET].value_counts().sort_index()
    labels = ["No asistio", "Asistio"]
    plt.figure(figsize=(5, 4))
    plt.bar(labels, [counts.get(0, 0), counts.get(1, 0)], color=["#ef4444", "#22c55e"])
    plt.title("Distribucion de la variable objetivo (asistencia)")
    plt.ylabel("Inscripciones")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "01_target_distribution.png", dpi=120)
    plt.close()


def _plot_attendance_by(df: pd.DataFrame, col: str, fname: str, title: str) -> None:
    grp = df.groupby(col)[TARGET].mean().sort_values(ascending=False)
    plt.figure(figsize=(7, 4))
    plt.bar(grp.index.astype(str), grp.values, color="#3b82f6")
    plt.title(title)
    plt.ylabel("Tasa de asistencia")
    plt.ylim(0, 1)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / fname, dpi=120)
    plt.close()


def _plot_feature_importances(importances: list[dict]) -> None:
    if not importances:
        return
    feats = [d["feature"] for d in importances][::-1]
    vals = [d["importance"] for d in importances][::-1]
    plt.figure(figsize=(8, 6))
    plt.barh(feats, vals, color="#8b5cf6")
    plt.title("Importancia de variables (modelo ganador)")
    plt.xlabel("Importancia")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "04_feature_importances.png", dpi=120)
    plt.close()


def _plot_confusion(cm: list[list[int]], model_name: str) -> None:
    import numpy as np

    cm_arr = np.array(cm)
    plt.figure(figsize=(4.5, 4))
    plt.imshow(cm_arr, cmap="Blues")
    plt.title(f"Matriz de confusion — {model_name}")
    plt.colorbar()
    ticks = ["No asistio", "Asistio"]
    plt.xticks([0, 1], ticks)
    plt.yticks([0, 1], ticks)
    plt.ylabel("Real")
    plt.xlabel("Prediccion")
    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(cm_arr[i, j]), ha="center", va="center",
                     color="white" if cm_arr[i, j] > cm_arr.max() / 2 else "black")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "05_confusion_matrix.png", dpi=120)
    plt.close()


def _plot_roc(roc: dict, auc: float, model_name: str) -> None:
    plt.figure(figsize=(5, 4))
    plt.plot(roc["fpr"], roc["tpr"], color="#16a34a", label=f"AUC = {auc:.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.title(f"Curva ROC — {model_name}")
    plt.xlabel("Tasa de falsos positivos")
    plt.ylabel("Tasa de verdaderos positivos")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "06_roc_curve.png", dpi=120)
    plt.close()


def run_pipeline(prefer_orm: bool = True, use_network: bool = True) -> dict:
    """Ejecuta las 6 fases CRISP-DM y devuelve el reporte completo."""
    ensure_dirs()

    # Fase 1
    business_understanding()

    # Fase 2
    raw, source = load_raw(prefer_orm=prefer_orm)
    data_understanding(raw, source)

    # Fase 3
    _print_header("Fase 3", "Preparacion de los datos")
    X, y, enriched = build_feature_matrix(raw, use_network=use_network)
    print(f"  Matriz de caracteristicas: {X.shape[0]} filas x {X.shape[1]} columnas")
    print(f"  Variables: {list(X.columns)}")
    print(f"  Eventos cerca de feriado: {enriched['near_holiday'].mean():.1%}")

    _plot_target_distribution(enriched)
    _plot_attendance_by(enriched, "category", "02_attendance_by_category.png",
                        "Tasa de asistencia por categoria")
    _plot_attendance_by(enriched, "near_holiday", "03_attendance_by_holiday.png",
                        "Asistencia: evento cerca de feriado (0=no, 1=si)")

    # Fase 4 + 5
    _print_header("Fase 4", "Modelado")
    report = train_and_evaluate(X, y)
    for name, m in report["results"].items():
        print(f"  {name:22s} | AUC={m['roc_auc']:.3f} | F1={m['f1']:.3f} | "
              f"Acc={m['accuracy']:.3f} | CV-AUC={m['cv_roc_auc_mean']:.3f}")

    _print_header("Fase 5", "Evaluacion")
    best = report["best_model_name"]
    best_metrics = report["results"][best]
    print(f"  Modelo ganador: {best}")
    print(f"  ROC-AUC: {best_metrics['roc_auc']:.3f} | F1: {best_metrics['f1']:.3f} | "
          f"Precision: {best_metrics['precision']:.3f} | Recall: {best_metrics['recall']:.3f}")
    meta = "ALCANZADA" if best_metrics["cv_roc_auc_mean"] >= 0.75 else "NO alcanzada"
    print(f"  Meta de negocio (CV-AUC >= 0.75): {meta}")

    _plot_feature_importances(report["feature_importances"])
    _plot_confusion(best_metrics["confusion_matrix"], best)
    _plot_roc(report["roc_curve"], best_metrics["roc_auc"], best)

    # Fase 6
    _print_header("Fase 6", "Despliegue")
    print(f"  Modelo persistido en: {report['model_path']}")
    print("  Expuesto via API Django: POST /api/analytics/predict-attendance/")
    print(f"  Graficos en: {PLOTS_DIR}")

    # Persistir metricas (sin objetos no serializables).
    serializable = {
        "source": source,
        "n_rows": int(len(raw)),
        "target_rate": round(float(y.mean()), 4),
        "best_model_name": report["best_model_name"],
        "results": report["results"],
        "feature_importances": report["feature_importances"],
        "model_path": report["model_path"],
    }
    METRICS_PATH.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Metricas en: {METRICS_PATH}")

    report["source"] = source
    return report
