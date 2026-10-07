import os

import psycopg
import pytest

from app.repository import PersistenceRepository


pytestmark = pytest.mark.integration


def test_optimization_persistence_is_atomic_and_idempotent():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")

    repository = PersistenceRepository()
    request = {
        "order": {
            "id": "integration-order-1",
            "origin": "PL-WRO",
            "destination": "PL-WAW",
            "weight_kg": 1000,
            "revenue_pln": 5000,
        }
    }
    result = {
        "decision": "approve",
        "reason": "target_margin_met",
        "vehicle_id": "V1",
        "carrier_id": "C1",
        "cost_pln": 1000,
        "margin_pln": 4000,
        "margin_pct": 80,
        "requires_approval": False,
        "audit_event": {
            "event_type": "order.optimization.completed",
            "aggregate_id": "integration-order-1",
            "actor": "integration-test",
            "payload": {"decision": "approve"},
            "occurred_at": "2026-01-01T00:00:00+00:00",
        },
    }

    first = repository.persist_optimization(
        idempotency_key="integration:test:1",
        actor_id="integration-test",
        request_payload=request,
        result=result,
    )
    second = repository.persist_optimization(
        idempotency_key="integration:test:1",
        actor_id="integration-test",
        request_payload=request,
        result=result,
    )

    assert first == second

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        order_count = conn.execute(
            "SELECT count(*) FROM orders WHERE id = %s",
            ("integration-order-1",),
        ).fetchone()[0]
        decision_count = conn.execute(
            "SELECT count(*) FROM optimization_decisions WHERE idempotency_key = %s",
            ("integration:test:1",),
        ).fetchone()[0]
        audit_count = conn.execute(
            "SELECT count(*) FROM audit_events WHERE aggregate_id = %s",
            ("integration-order-1",),
        ).fetchone()[0]
        outbox_count = conn.execute(
            "SELECT count(*) FROM outbox_events WHERE aggregate_id = %s",
            ("integration-order-1",),
        ).fetchone()[0]

    assert order_count == 1
    assert decision_count == 1
    assert audit_count == 1
    assert outbox_count == 1

    conflicting_request = {
        **request,
        "order": {**request["order"], "revenue_pln": 6000},
    }
    with pytest.raises(Exception, match="different request"):
        repository.persist_optimization(
            idempotency_key="integration:test:1",
            actor_id="integration-test",
            request_payload=conflicting_request,
            result=result,
        )
