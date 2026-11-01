import os
from uuid import uuid4

import psycopg
import pytest

from app import migrate
from app.jobs import claim_job, enqueue_job, fail_job, finish_job
from app.worker import run_once


@pytest.fixture
def migrated_database():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    migrate.main()
    yield


@pytest.mark.integration
def test_enqueue_is_idempotent_and_conflicts_on_changed_payload(migrated_database):
    key = "job-" + str(uuid4())
    first = enqueue_job(idempotency_key=key, task_type="health_check", payload={})
    replay = enqueue_job(idempotency_key=key, task_type="health_check", payload={})
    assert first["id"] == replay["id"]
    with pytest.raises(ValueError, match="different job data"):
        enqueue_job(idempotency_key=key, task_type="health_check", payload={"x": 1})


@pytest.mark.integration
def test_worker_completes_registered_task(migrated_database):
    key = "job-" + str(uuid4())
    queued = enqueue_job(idempotency_key=key, task_type="health_check", payload={})
    assert run_once(worker_id="test-worker") is True
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        row = conn.execute("SELECT status, result, attempts FROM jobs WHERE id = %s",
                           (queued["id"],)).fetchone()
    assert row == ("succeeded", {"ok": True}, 1)


@pytest.mark.integration
def test_failure_retries_then_dead_letters(migrated_database):
    queued = enqueue_job(idempotency_key="job-" + str(uuid4()),
                         task_type="health_check", payload={}, max_attempts=2)
    first = claim_job(worker_id="worker-a")
    assert first["id"] == queued["id"]
    assert fail_job(job_id=first["id"], worker_id="worker-a",
                    error="temporary failure", retry_delay_seconds=1) == "pending"
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("UPDATE jobs SET available_at = now() - interval '1 second' WHERE id = %s",
                     (queued["id"],))
    second = claim_job(worker_id="worker-b")
    assert second["attempts"] == 2
    assert fail_job(job_id=second["id"], worker_id="worker-b",
                    error="permanent failure", retry_delay_seconds=1) == "dead_letter"


@pytest.mark.integration
def test_stale_worker_cannot_complete_after_lease_is_lost(migrated_database):
    queued = enqueue_job(idempotency_key="job-" + str(uuid4()),
                         task_type="health_check", payload={})
    job = claim_job(worker_id="worker-a", lease_seconds=5)
    assert job["id"] == queued["id"]
    assert finish_job(job_id=job["id"], worker_id="wrong-worker", result={"ok": True}) is False
    assert finish_job(job_id=job["id"], worker_id="worker-a", result={"ok": True}) is True
