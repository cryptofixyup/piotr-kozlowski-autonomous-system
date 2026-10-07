import hmac
import os
from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class ActorContext:
    actor_id: str


def require_actor(
    authorization: str | None = Header(default=None),
) -> ActorContext:
    configured_token = os.getenv("AUTONOMOUS_API_TOKEN")
    configured_actor = os.getenv("AUTONOMOUS_ACTOR_ID", "api-client")

    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
        )

    supplied_token = authorization.removeprefix("Bearer ")
    if not hmac.compare_digest(supplied_token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return ActorContext(actor_id=configured_actor)
