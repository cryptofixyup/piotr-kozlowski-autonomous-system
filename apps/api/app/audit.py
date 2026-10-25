from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from typing import Any

@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    aggregate_id: str
    actor: str
    payload: dict[str, Any]
    occurred_at: str

def build_audit_event(event_type: str, aggregate_id: str, actor: str, payload: dict[str, Any]) -> dict[str, Any]:
    event = AuditEvent(event_type, aggregate_id, actor, payload, datetime.now(timezone.utc).isoformat())
    return asdict(event)

def serialize_audit_event(event: dict[str, Any]) -> str:
    return json.dumps(event, separators=(",", ":"), sort_keys=True)
