from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.jobs import JobConflict, enqueue_job
from app.optimizer import InvalidEconomics, optimize_order
from app.repository import IdempotencyConflict, PersistenceRepository
from app.schemas import JobRequest, OptimizeRequest
from app.security import ActorContext, require_actor

app = FastAPI(title="Autonomous Operations API", version="0.3.0")
repository = PersistenceRepository()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/jobs", status_code=status.HTTP_202_ACCEPTED)
def submit_job(
    request: JobRequest,
    actor: ActorContext = Depends(require_actor),
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ] = "",
):
    if not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="Idempotency-Key must not be empty")
    try:
        job = enqueue_job(
            idempotency_key=f"{actor.actor_id}:{idempotency_key}",
            task_type=request.task_type,
            payload=request.payload,
            max_attempts=request.max_attempts,
        )
        return job
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (RuntimeError, psycopg.Error) as exc:
        raise HTTPException(status_code=503, detail="Persistent job queue unavailable") from exc


@app.post("/v1/optimize")
def optimize(
    request: OptimizeRequest,
    actor: ActorContext = Depends(require_actor),
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ] = "",
):
    if not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not be empty",
        )

    try:
        result = optimize_order(request, actor_id=actor.actor_id)
    except InvalidEconomics as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return repository.persist_optimization(
            idempotency_key=idempotency_key,
            actor_id=actor.actor_id,
            request_payload=request.model_dump(mode="json"),
            result=result,
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (RuntimeError, psycopg.Error) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistent operation unavailable",
        ) from exc
