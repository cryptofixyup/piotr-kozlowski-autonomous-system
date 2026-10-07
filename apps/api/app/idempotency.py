import hashlib
import json
from typing import Any

def make_idempotency_key(operation: str, payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"{operation}:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
