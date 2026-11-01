"""Single-cycle worker. Only explicitly registered task handlers can run."""
from __future__ import annotations

import argparse
import os
import socket
from typing import Any, Callable

from .jobs import claim_job, fail_job, finish_job

TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]


def health_check(payload: dict[str, Any]) -> dict[str, Any]:
    """A deterministic example handler; proves the queue without side effects."""
    if payload:
        raise ValueError("health_check accepts an empty payload")
    return {"ok": True}


HANDLERS: dict[str, TaskHandler] = {"health_check": health_check}


def run_once(*, worker_id: str, handlers: dict[str, TaskHandler] | None = None) -> bool:
    job = claim_job(worker_id=worker_id)
    if job is None:
        return False
    registry = HANDLERS if handlers is None else handlers
    handler = registry.get(job["task_type"])
    if handler is None:
        fail_job(job_id=job["id"], worker_id=worker_id,
                 error="unregistered task type: " + job["task_type"],
                 retry_delay_seconds=1)
        return True
    try:
        result = handler(job["payload"])
        if not isinstance(result, dict):
            raise TypeError("task handler must return a JSON object")
        if not finish_job(job_id=job["id"], worker_id=worker_id, result=result):
            # The lease expired or was reclaimed. Do not overwrite the newer owner.
            return True
    except Exception as exc:
        fail_job(job_id=job["id"], worker_id=worker_id,
                 error=f"{type(exc).__name__}: {exc}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one durable autonomous job")
    parser.add_argument("--worker-id", default=f"{socket.gethostname()}:{os.getpid()}")
    args = parser.parse_args()
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required")
    print("job_claimed=" + str(run_once(worker_id=args.worker_id)).lower())


if __name__ == "__main__":
    main()
