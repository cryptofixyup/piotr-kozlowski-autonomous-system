import hashlib
import json
from typing import Any


def make_idempotency_key(operation: str, payload: Any) -> str:
    """Return a deterministic key for a JSON-safe payload.

    Callers must pass JSON-serializable values. Values such as UUID, Decimal,
    and datetime must be normalized by the caller before hashing so distinct
    semantic values cannot be collapsed by an implicit string conversion.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"{operation}:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def make_request_hash(payload: Any) -> str:
    """Hash a JSON-safe request payload for idempotency conflict detection."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
