"""
Fase 6 de CRISP-DM: Despliegue.

Expone el modelo entrenado y la analitica descriptiva como endpoints REST,
integrados al resto de la API de CertyPro.

Endpoints:
    GET  /api/analytics/dashboard/           -> estadisticas descriptivas
    POST /api/analytics/predict-attendance/  -> prediccion de asistencia
    GET  /api/analytics/model-info/          -> metricas del modelo entrenado
"""

from __future__ import annotations

import json

import pandas as pd
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .crispdm.config import FEATURE_COLUMNS, METRICS_PATH, TARGET
from .crispdm.data_source import load_raw
from .crispdm.model import load_model


class DashboardView(APIView):
    """Estadisticas descriptivas de asistencia (analitica de negocio)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        raw, source = load_raw(prefer_orm=True)
        if raw.empty:
            return Response({"detail": "Sin datos disponibles."}, status=status.HTTP_204_NO_CONTENT)

        df = raw.copy()
        df["event_date"] = pd.to_datetime(df["event_date"])
        by_category = df.groupby("category")[TARGET].mean().round(3).to_dict()
        by_month = df.groupby(df["event_date"].dt.to_period("M").astype(str))[TARGET].mean().round(3).to_dict()

        return Response(
            {
                "source": source,
                "total_enrollments": int(len(df)),
                "unique_participants": int(df["participant_id"].nunique()),
                "unique_events": int(df["event_id"].nunique()),
                "global_attendance_rate": round(float(df[TARGET].mean()), 3),
                "attendance_by_category": by_category,
                "attendance_by_month": by_month,
            }
        )


class ModelInfoView(APIView):
    """Devuelve las metricas del ultimo entrenamiento (metrics.json)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not METRICS_PATH.exists():
            return Response(
                {"detail": "Modelo no entrenado. Ejecute: python manage.py crispdm_train"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(json.loads(METRICS_PATH.read_text(encoding="utf-8")))


class PredictAttendanceView(APIView):
    """
    Predice la probabilidad de asistencia de una inscripcion.

    Cuerpo (JSON) con las caracteristicas; faltantes se completan con valores
    por defecto razonables:
        {
          "duration_hours": 8, "max_capacity": 50, "is_public": 1,
          "category": "Tecnologia", "event_dow": 2, "event_month": 7,
          "lead_time_days": 10, "near_holiday": 0, "was_invited": 1,
          "invitation_accepted": 1, "participant_prior_events": 3,
          "participant_prior_rate": 0.8
        }
    """

    permission_classes = [permissions.IsAuthenticated]

    _defaults = {
        "duration_hours": 8,
        "max_capacity": 50,
        "is_public": 0,
        "category": "Tecnologia",
        "event_dow": 2,
        "event_month": 6,
        "lead_time_days": 7,
        "near_holiday": 0,
        "was_invited": 1,
        "invitation_accepted": 0,
        "participant_prior_events": 0,
        "participant_prior_rate": 0.5,
    }

    def post(self, request):
        try:
            model = load_model()
        except (FileNotFoundError, OSError):
            return Response(
                {"detail": "Modelo no entrenado. Ejecute: python manage.py crispdm_train"},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {**self._defaults, **(request.data or {})}
        row = {col: payload.get(col, self._defaults.get(col)) for col in FEATURE_COLUMNS}
        X = pd.DataFrame([row], columns=FEATURE_COLUMNS)

        proba = float(model.predict_proba(X)[0, 1])
        pred = int(proba >= 0.5)
        return Response(
            {
                "will_attend": bool(pred),
                "attendance_probability": round(proba, 4),
                "risk_level": "alto" if proba < 0.4 else ("medio" if proba < 0.7 else "bajo"),
                "recommendation": (
                    "Enviar recordatorio prioritario" if proba < 0.4
                    else "Seguimiento normal" if proba < 0.7
                    else "Sin accion requerida"
                ),
                "features_used": row,
            }
        )
