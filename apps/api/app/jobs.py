"""PostgreSQL-backed durable queue with idempotency and bounded leases/retries."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from .database import transaction


class JobConflict(ValueError):
    """An idempotency key was reused for a different job."""


def enqueue_job(*, idempotency_key: str, task_type: str, payload: dict[str, Any],
                max_attempts: int = 3) -> dict[str, Any]:
    if not idempotency_key or len(idempotency_key) > 200:
        raise ValueError("idempotency_key must contain 1-200 characters")
    if not task_type or len(task_type) > 100:
        raise ValueError("task_type must contain 1-100 characters")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if not 1 <= max_attempts <= 10:
        raise ValueError("max_attempts must be between 1 and 10")

    with transaction() as conn:
        row = conn.execute(
            """INSERT INTO jobs (idempotency_key, task_type, payload, max_attempts)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (idempotency_key) DO NOTHING
               RETURNING id, task_type, payload, status, attempts, max_attempts""",
            (idempotency_key, task_type, Jsonb(payload), max_attempts),
        ).fetchone()
        if row is None:
            row = conn.execute(
                """SELECT id, task_type, payload, status, attempts, max_attempts
                   FROM jobs WHERE idempotency_key = %s FOR UPDATE""",
                (idempotency_key,),
            ).fetchone()
            if row is None:
                raise RuntimeError("job idempotency record disappeared")
            if row[1] != task_type or row[2] != payload or row[5] != max_attempts:
                raise JobConflict("idempotency key was reused with different job data")
        else:
            conn.execute(
                "INSERT INTO job_events (job_id, event_type, payload) VALUES (%s, %s, %s)",
                (row[0], "job.queued", Jsonb({"task_type": task_type})),
            )
        return {"id": str(row[0]), "task_type": row[1], "payload": row[2],
                "status": row[3], "attempts": row[4], "max_attempts": row[5]}


def claim_job(*, worker_id: str, lease_seconds: int = 60) -> dict[str, Any] | None:
    if not worker_id or len(worker_id) > 128:
        raise ValueError("worker_id must contain 1-128 characters")
    if not 5 <= lease_seconds <= 900:
        raise ValueError("lease_seconds must be between 5 and 900")
    with transaction() as conn:
        row = conn.execute(
            """WITH candidate AS (
                   SELECT id FROM jobs
                   WHERE (status = 'pending' AND available_at <= now())
                      OR (status = 'running' AND lease_expires_at < now()
                          AND attempts < max_attempts)
                   ORDER BY available_at, created_at
                   FOR UPDATE SKIP LOCKED LIMIT 1
               )
               UPDATE jobs AS j
               SET status = 'running', attempts = j.attempts + 1,
                   worker_id = %s,
                   lease_expires_at = now() + (%s * interval '1 second'),
                   started_at = COALESCE(j.started_at, now()), updated_at = now()
               FROM candidate WHERE j.id = candidate.id
               RETURNING j.id, j.task_type, j.payload, j.attempts, j.max_attempts""",
            (worker_id, lease_seconds),
        ).fetchone()
        if row is None:
            # A crashed worker may have exhausted its attempts while holding a lease.
            conn.execute(
                """UPDATE jobs SET status = 'dead_letter', worker_id = NULL,
                       lease_expires_at = NULL, completed_at = now(), updated_at = now(),
                       last_error = COALESCE(last_error, 'worker lease expired; attempts exhausted')
                   WHERE status = 'running' AND lease_expires_at < now()
                     AND attempts >= max_attempts"""
            )
            return None
        conn.execute(
            "INSERT INTO job_events (job_id, event_type, payload) VALUES (%s, %s, %s)",
            (row[0], "job.claimed", Jsonb({"worker_id": worker_id, "attempt": row[3]})),
        )
        return {"id": str(row[0]), "task_type": row[1], "payload": row[2],
                "attempts": row[3], "max_attempts": row[4]}


def finish_job(*, job_id: str, worker_id: str, result: dict[str, Any]) -> bool:
    with transaction() as conn:
        row = conn.execute(
            """UPDATE jobs SET status = 'succeeded', result = %s, worker_id = NULL,
                   lease_expires_at = NULL, completed_at = now(), updated_at = now()
               WHERE id = %s AND status = 'running' AND worker_id = %s
                   AND lease_expires_at > now()
               RETURNING id""",
            (Jsonb(result), UUID(job_id), worker_id),
        ).fetchone()
        if row is None:
            return False
        conn.execute(
            "INSERT INTO job_events (job_id, event_type, payload) VALUES (%s, %s, %s)",
            (row[0], "job.succeeded", Jsonb(result)),
        )
        return True


def fail_job(*, job_id: str, worker_id: str, error: str, retry_delay_seconds: int = 5) -> str:
    if not 1 <= retry_delay_seconds <= 3600:
        raise ValueError("retry_delay_seconds must be between 1 and 3600")
    safe_error = error[:1000]
    with transaction() as conn:
        row = conn.execute(
            """UPDATE jobs SET
                   status = CASE WHEN attempts >= max_attempts THEN 'dead_letter' ELSE 'pending' END,
                   available_at = now() + (%s * interval '1 second'),
                   worker_id = NULL, lease_expires_at = NULL,
                   last_error = %s,
                   completed_at = CASE WHEN attempts >= max_attempts THEN now() ELSE NULL END,
                   updated_at = now()
               WHERE id = %s AND status = 'running' AND worker_id = %s
               RETURNING id, status, attempts""",
            (retry_delay_seconds, safe_error, UUID(job_id), worker_id),
        ).fetchone()
        if row is None:
            return "lease_lost"
        conn.execute(
            "INSERT INTO job_events (job_id, event_type, payload) VALUES (%s, %s, %s)",
            (row[0], "job." + row[1], Jsonb({"error": safe_error, "attempt": row[2]})),
        )
        return row[1]
