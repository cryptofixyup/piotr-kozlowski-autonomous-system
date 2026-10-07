import json
from typing import Any

from psycopg.types.json import Jsonb

from .database import transaction
from .idempotency import make_request_hash


class IdempotencyConflict(Exception):
    pass


class PersistenceRepository:
    def persist_optimization(
        self,
        *,
        idempotency_key: str,
        actor_id: str,
        request_payload: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        request_hash = make_request_hash(request_payload)

        with transaction() as conn:
            inserted = conn.execute(
                """
                INSERT INTO idempotency_keys
                    (key, operation, request_hash, actor_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (key) DO NOTHING
                RETURNING key
                """,
                (idempotency_key, "optimize", request_hash, actor_id),
            ).fetchone()

            if inserted is None:
                existing = conn.execute(
                    """
                    SELECT request_hash, actor_id, response_json
                    FROM idempotency_keys
                    WHERE key = %s
                    FOR UPDATE
                    """,
                    (idempotency_key,),
                ).fetchone()
                if existing is None:
                    raise RuntimeError("idempotency record disappeared")
                if existing[0] != request_hash:
                    raise IdempotencyConflict("Idempotency-Key was reused with a different request")
                if existing[1] != actor_id:
                    raise IdempotencyConflict("Idempotency-Key belongs to a different actor")
                if existing[2] is None:
                    raise RuntimeError("idempotency record has no committed response")
                return existing[2]

            order = request_payload["order"]
            conn.execute(
                """
                INSERT INTO orders
                    (id, external_ref, origin, destination, weight_kg, revenue_pln)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    origin = EXCLUDED.origin,
                    destination = EXCLUDED.destination,
                    weight_kg = EXCLUDED.weight_kg,
                    revenue_pln = EXCLUDED.revenue_pln,
                    updated_at = now()
                """,
                (
                    order["id"],
                    order["id"],
                    order["origin"],
                    order["destination"],
                    order["weight_kg"],
                    order["revenue_pln"],
                ),
            )

            conn.execute(
                """
                INSERT INTO optimization_decisions
                    (order_id, decision, reason, vehicle_id, carrier_id,
                     cost_pln, margin_pln, margin_pct, requires_approval, idempotency_key)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    order["id"],
                    result["decision"],
                    result["reason"],
                    result.get("vehicle_id"),
                    result.get("carrier_id"),
                    result.get("cost_pln"),
                    result.get("margin_pln"),
                    result.get("margin_pct"),
                    result["requires_approval"],
                    idempotency_key,
                ),
            )

            audit_event = result["audit_event"]
            conn.execute(
                """
                INSERT INTO audit_events
                    (event_type, aggregate_id, actor, payload, occurred_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    audit_event["event_type"],
                    audit_event["aggregate_id"],
                    actor_id,
                    Jsonb(audit_event["payload"]),
                    audit_event["occurred_at"],
                ),
            )

            outbox_payload = {
                "decision": result,
                "actor_id": actor_id,
                "request_hash": request_hash,
            }
            conn.execute(
                """
                INSERT INTO outbox_events
                    (aggregate_id, event_type, payload)
                VALUES (%s, %s, %s)
                """,
                (order["id"], "order.optimization.completed", Jsonb(outbox_payload)),
            )

            response_json = json.loads(json.dumps(result))
            conn.execute(
                """
                UPDATE idempotency_keys
                SET response_json = %s
                WHERE key = %s
                """,
                (Jsonb(response_json), idempotency_key),
            )

        return response_json
