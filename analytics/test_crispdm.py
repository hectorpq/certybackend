"""Tests del modulo analytics (pipeline CRISP-DM + endpoints REST)."""

import json
from datetime import date
from unittest import mock

import pandas as pd
import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from analytics.crispdm import config, data_source, features, holidays_api, model, pipeline


@pytest.fixture
def tmp_outputs(tmp_path, monkeypatch):
    """Redirige todas las rutas de salida a un directorio temporal."""
    outputs = tmp_path / "outputs"
    models_dir = tmp_path / "models"
    plots = outputs / "plots"
    cache = outputs / "holidays_cache.json"
    model_path = models_dir / "attendance_model.joblib"
    metrics = outputs / "metrics.json"

    def _ensure_dirs():
        for d in (outputs, models_dir, plots):
            d.mkdir(parents=True, exist_ok=True)

    for mod in (config, holidays_api, model, pipeline):
        monkeypatch.setattr(mod, "ensure_dirs", _ensure_dirs, raising=False)
    monkeypatch.setattr(holidays_api, "HOLIDAYS_CACHE", cache)
    monkeypatch.setattr(model, "MODEL_PATH", model_path)
    monkeypatch.setattr(pipeline, "PLOTS_DIR", plots)
    monkeypatch.setattr(pipeline, "METRICS_PATH", metrics)
    _ensure_dirs()
    return {"cache": cache, "model": model_path, "metrics": metrics, "plots": plots}


@pytest.fixture
def small_raw():
    return data_source.from_synthetic(n_participants=120, n_events=15)


# ─── data_source ────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_from_synthetic_is_deterministic_and_has_columns():
    a = data_source.from_synthetic(n_participants=50, n_events=5)
    b = data_source.from_synthetic(n_participants=50, n_events=5)
    assert list(a.columns) == data_source.RAW_COLUMNS
    assert len(a) > 0
    pd.testing.assert_frame_equal(a, b)
    assert set(a["attended"].unique()) <= {0, 1}


@pytest.mark.unit
def test_load_raw_without_orm_uses_synthetic():
    df, source = data_source.load_raw(prefer_orm=False)
    assert source == "synthetic"
    assert not df.empty


@pytest.mark.unit
def test_load_raw_falls_back_when_orm_fails(capsys):
    with mock.patch.object(data_source, "from_orm", side_effect=RuntimeError("boom")):
        df, source = data_source.load_raw(prefer_orm=True)
    assert source == "synthetic"
    assert "boom" in capsys.readouterr().out


@pytest.mark.unit
def test_load_raw_uses_orm_when_enough_rows(small_raw):
    with mock.patch.object(data_source, "from_orm", return_value=small_raw):
        df, source = data_source.load_raw(prefer_orm=True, min_rows=1)
    assert source == "orm"
    assert len(df) == len(small_raw)


@pytest.mark.django_db
def test_from_orm_empty_db_returns_empty_frame():
    df = data_source.from_orm()
    assert df.empty
    assert list(df.columns) == data_source.RAW_COLUMNS


@pytest.mark.unit
def test_from_orm_builds_rows_from_enrollments():
    ev = mock.Mock(
        id=7,
        event_date=date(2024, 7, 28),
        duration_hours=8,
        max_capacity=30,
        is_public=True,
    )
    ev.category.name = "Salud"
    inv = mock.Mock(status="accepted")
    enrollment = mock.Mock(id=1, participant_id=3, event=ev, invitation=inv, attendance=True, enrolled_at=None)
    skipped = mock.Mock(event=None)

    qs = mock.Mock()
    qs.iterator.return_value = [enrollment, skipped]
    manager = mock.Mock()
    manager.select_related.return_value.all.return_value = qs

    with mock.patch("events.models.Enrollment.objects", manager):
        df = data_source.from_orm()

    assert len(df) == 1
    row = df.iloc[0]
    assert row["category"] == "Salud"
    assert row["invitation_accepted"] == 1
    assert row["attended"] == 1
    assert row["enrolled_at"] == date(2024, 7, 28)


# ─── holidays_api ───────────────────────────────────────────────────────────


@pytest.mark.unit
def test_get_holidays_from_api_and_cache(tmp_outputs):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = [{"date": "2024-07-28"}, {"name": "sin fecha"}]
    with mock.patch.object(holidays_api.requests, "get", return_value=resp):
        out = holidays_api.get_holiday_dates(years=(2024,), country="PE")
    assert date(2024, 7, 28) in out
    cached = json.loads(tmp_outputs["cache"].read_text(encoding="utf-8"))
    assert cached["PE-2024"] == ["2024-07-28"]

    # Sin red: debe usar la cache guardada.
    out2 = holidays_api.get_holiday_dates(years=(2024,), country="PE", use_network=False)
    assert out2 == {date(2024, 7, 28)}


@pytest.mark.unit
def test_get_holidays_fallback_when_api_fails(tmp_outputs):
    with mock.patch.object(holidays_api.requests, "get", side_effect=requests.ConnectionError()):
        out = holidays_api.get_holiday_dates(years=(2023,), country="PE")
    assert date(2023, 12, 25) in out
    assert len(out) == len(holidays_api._PERU_FIXED)


@pytest.mark.unit
def test_holidays_corrupt_cache_and_bad_dates(tmp_outputs):
    tmp_outputs["cache"].write_text("{not json", encoding="utf-8")
    assert holidays_api._load_cache() == {}

    tmp_outputs["cache"].write_text(json.dumps({"PE-2025": ["2025-01-01", "invalid"]}), encoding="utf-8")
    out = holidays_api.get_holiday_dates(years=(2025,), country="PE", use_network=False)
    assert out == {date(2025, 1, 1)}


# ─── features ───────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_build_feature_matrix(small_raw):
    with mock.patch.object(features, "get_holiday_dates", return_value={date(2024, 7, 28)}):
        X, y, enriched = features.build_feature_matrix(small_raw, use_network=False)
    assert list(X.columns) == config.FEATURE_COLUMNS
    assert len(X) == len(y) == len(small_raw)
    assert (X["lead_time_days"] >= 0).all()
    assert set(enriched["near_holiday"].unique()) <= {0, 1}
    assert X["participant_prior_rate"].between(0, 1).all()


# ─── model + pipeline + management command ──────────────────────────────────


@pytest.fixture
def trained(tmp_outputs, small_raw):
    with (
        mock.patch.object(pipeline, "load_raw", return_value=(small_raw, "synthetic")),
        mock.patch.object(features, "get_holiday_dates", return_value=set()),
    ):
        report = pipeline.run_pipeline(prefer_orm=False, use_network=False)
    return report, tmp_outputs


@pytest.mark.unit
def test_run_pipeline_end_to_end(trained):
    report, paths = trained
    assert report["best_model_name"] in report["results"]
    assert report["source"] == "synthetic"
    assert paths["model"].exists()
    metrics = json.loads(paths["metrics"].read_text(encoding="utf-8"))
    assert metrics["n_rows"] > 0
    assert any(paths["plots"].glob("*.png"))

    loaded = model.load_model()
    assert hasattr(loaded, "predict_proba")


@pytest.mark.unit
def test_feature_importances_edge_cases():
    no_names = mock.Mock()
    no_names.get_feature_names_out.side_effect = ValueError()
    pipe = mock.Mock(named_steps={"clf": object(), "pre": no_names})
    assert model._feature_importances(pipe) is None

    pre = mock.Mock()
    pre.get_feature_names_out.return_value = ["a"]
    pipe = mock.Mock(named_steps={"clf": object(), "pre": pre})
    assert model._feature_importances(pipe) is None

    pipeline._plot_feature_importances([])  # no debe fallar ni graficar


# ─── views ──────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client(db):
    user = get_user_model().objects.create_user(email="analytics@test.com", full_name="Analytics", password="x")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_dashboard_view(api_client, small_raw):
    with mock.patch("analytics.views.load_raw", return_value=(small_raw, "synthetic")):
        resp = api_client.get("/api/analytics/dashboard/")
    assert resp.status_code == 200
    assert resp.data["source"] == "synthetic"
    assert resp.data["total_enrollments"] == len(small_raw)
    assert resp.data["attendance_by_category"]


@pytest.mark.django_db
def test_dashboard_view_empty(api_client):
    empty = pd.DataFrame(columns=data_source.RAW_COLUMNS)
    with mock.patch("analytics.views.load_raw", return_value=(empty, "orm")):
        resp = api_client.get("/api/analytics/dashboard/")
    assert resp.status_code == 204


@pytest.mark.django_db
def test_model_info_view(api_client, tmp_path):
    missing = tmp_path / "missing.json"
    with mock.patch("analytics.views.METRICS_PATH", missing):
        assert api_client.get("/api/analytics/model-info/").status_code == 404

    missing.write_text(json.dumps({"best_model_name": "random_forest"}), encoding="utf-8")
    with mock.patch("analytics.views.METRICS_PATH", missing):
        resp = api_client.get("/api/analytics/model-info/")
    assert resp.status_code == 200
    assert resp.data["best_model_name"] == "random_forest"


@pytest.mark.django_db
def test_predict_attendance_view_without_model(api_client):
    with mock.patch("analytics.views.load_model", side_effect=FileNotFoundError()):
        resp = api_client.post("/api/analytics/predict-attendance/", {}, format="json")
    assert resp.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    "proba,risk",
    [(0.2, "alto"), (0.55, "medio"), (0.9, "bajo")],
)
def test_predict_attendance_view_risk_levels(api_client, proba, risk):
    import numpy as np

    fake = mock.Mock()
    fake.predict_proba.return_value = np.array([[1 - proba, proba]])
    with mock.patch("analytics.views.load_model", return_value=fake):
        resp = api_client.post("/api/analytics/predict-attendance/", {"duration_hours": 4}, format="json")
    assert resp.status_code == 200
    assert resp.data["risk_level"] == risk
    assert resp.data["will_attend"] is (proba >= 0.5)
    assert resp.data["features_used"]["duration_hours"] == 4
