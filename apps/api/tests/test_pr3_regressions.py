import copy
import os
from uuid import uuid4
from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import migrate
from app.main import optimize
from app.optimizer import optimize_order
from app.repository import PersistenceRepository
from app.schemas import OptimizeRequest
from app.security import ActorContext, require_actor


def request_data():
    return {
        "order": {"id": str(uuid4()), "origin": "WRO", "destination": "WAW",
                  "weight_kg": 100, "revenue_pln": 5000},
        "route": {"distance_km": 100, "toll_cost_pln": 0},
        "vehicles": [{"id": "V1", "capacity_kg": 1000, "fuel_l_per_100km": 10, "available": True}],
        "carriers": [{"id": "C1", "rating": 5, "cost_per_km": 1,
                      "availability": 1, "verified": True}],
        "fuel_price_pln_per_litre": 6,
        "target_margin_pct": 20,
    }


def test_non_ascii_token_returns_401(monkeypatch):
    monkeypatch.setenv("AUTONOMOUS_API_TOKEN", "configured")
    with pytest.raises(HTTPException) as exc:
        require_actor("Bearer é")
    assert exc.value.status_code == 401


@pytest.mark.parametrize("missing", [False, True])
def test_empty_or_missing_migrations_fail(monkeypatch, tmp_path, missing):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused")
    monkeypatch.setenv("MIGRATIONS_PATH", str(tmp_path / "missing" if missing else tmp_path))
    # Only the external connection is replaced; exercise migration discovery/error handling.
    monkeypatch.setattr(migrate.psycopg, "connect", MagicMock())
    with pytest.raises(RuntimeError, match="No SQL migrations"):
        migrate.main()


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_nonfinite_request_is_invalid(value):
    data = request_data()
    data["order"]["revenue_pln"] = value
    with pytest.raises(ValidationError):
        OptimizeRequest(**data)


def test_arithmetic_overflow_returns_422():
    data = request_data()
    data["route"]["distance_km"] = 1e308
    data["fuel_price_pln_per_litre"] = 1e308
    with pytest.raises(HTTPException) as exc:
        optimize(OptimizeRequest(**data), ActorContext("tester"), "overflow-test")
    assert exc.value.status_code == 422


@pytest.fixture
def database():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        yield conn


def persist(data, key):
    req = OptimizeRequest(**data)
    return PersistenceRepository().persist_optimization(
        idempotency_key=key, actor_id="regression-test",
        request_payload=req.model_dump(mode="json"),
        result=optimize_order(req, actor_id="regression-test"),
    )


@pytest.mark.integration
def test_decisions_retain_original_requests(database):
    first = request_data()
    second = copy.deepcopy(first)
    second["order"].update(origin="BER", revenue_pln=6000)
    key1, key2 = str(uuid4()), str(uuid4())
    original_response = persist(first, key1)
    persist(second, key2)
    assert persist(first, key1) == original_response
    snapshots = dict(database.execute(
        "SELECT idempotency_key, request_snapshot FROM optimization_decisions "
        "WHERE order_id = %s", (first["order"]["id"],),
    ).fetchall())
    assert snapshots[key1] == first
    assert snapshots[key2] == second
    assert database.execute("SELECT origin FROM orders WHERE id = %s",
                            (first["order"]["id"],)).fetchone()[0] == "BER"
    with pytest.raises(psycopg.errors.CheckViolation, match="immutable"):
        with database.transaction():
            database.execute(
                "UPDATE optimization_decisions SET request_snapshot = '{}'::jsonb "
                "WHERE idempotency_key = %s", (key1,),
            )
    assert database.execute(
        "SELECT request_snapshot FROM optimization_decisions WHERE idempotency_key = %s",
        (key1,),
    ).fetchone()[0] == first


@pytest.mark.integration
@pytest.mark.parametrize("revenue,weight", [(1e-8, 100), (1e14, 100), (5000, 0.001)])
def test_accepted_numbers_persist_without_overflow_or_rounding_to_zero(database, revenue, weight):
    data = request_data()
    data["order"].update(revenue_pln=revenue, weight_kg=weight)
    key = str(uuid4())
    result = persist(data, key)
    if revenue == 1e-8:
        assert result["decision"] == "reject"
        assert result["reason"] == "negative_margin"
    row = database.execute(
        "SELECT revenue_pln, weight_kg FROM orders WHERE id = %s",
        (data["order"]["id"],),
    ).fetchone()
    assert float(row[0]) == revenue
    assert float(row[1]) == weight
    assert database.execute("SELECT count(*) FROM audit_events WHERE aggregate_id = %s",
                            (data["order"]["id"],)).fetchone()[0] == 1
    assert database.execute("SELECT count(*) FROM outbox_events WHERE aggregate_id = %s",
                            (data["order"]["id"],)).fetchone()[0] == 1
