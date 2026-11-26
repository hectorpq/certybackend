"""Rutas de la app analytics (fase de Despliegue CRISP-DM)."""

from django.urls import path

from .views import DashboardView, ModelInfoView, PredictAttendanceView

app_name = "analytics"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("predict-attendance/", PredictAttendanceView.as_view(), name="predict-attendance"),
    path("model-info/", ModelInfoView.as_view(), name="model-info"),
]
