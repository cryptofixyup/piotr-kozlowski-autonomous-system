import pytest
from fastapi import HTTPException

from app.security import require_actor


def test_missing_credential_configuration_is_unavailable(monkeypatch):
    monkeypatch.delenv("AUTONOMOUS_API_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc:
        require_actor("Bearer anything")
    assert exc.value.status_code == 503


def test_invalid_bearer_is_unauthorized(monkeypatch):
    monkeypatch.setenv("AUTONOMOUS_API_TOKEN", "configured")
    monkeypatch.setenv("AUTONOMOUS_ACTOR_ID", "actor-1")
    with pytest.raises(HTTPException) as exc:
        require_actor("Bearer wrong")
    assert exc.value.status_code == 401


def test_valid_bearer_resolves_configured_actor(monkeypatch):
    monkeypatch.setenv("AUTONOMOUS_API_TOKEN", "configured")
    monkeypatch.setenv("AUTONOMOUS_ACTOR_ID", "actor-1")
    actor = require_actor("Bearer configured")
    assert actor.actor_id == "actor-1"


def test_non_bearer_is_unauthorized(monkeypatch):
    monkeypatch.setenv("AUTONOMOUS_API_TOKEN", "configured")
    with pytest.raises(HTTPException) as exc:
        require_actor("Basic configured")
    assert exc.value.status_code == 401
