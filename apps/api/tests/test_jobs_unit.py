from app.jobs import JobConflict
from app.worker import health_check


def test_health_check_is_deterministic_and_side_effect_free():
    assert health_check({}) == {"ok": True}


def test_health_check_rejects_unexpected_payload():
    try:
        health_check({"command": "anything"})
    except ValueError as exc:
        assert "empty payload" in str(exc)
    else:
        raise AssertionError("unexpected payload accepted")


def test_job_conflict_is_a_distinct_error():
    assert issubclass(JobConflict, ValueError)
