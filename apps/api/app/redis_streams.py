OUTBOX_STREAM = "outbox:events"
EXECUTION_GROUP = "execution-workers"


def create_execution_consumer_group(redis_client) -> None:
    """Create the future execution consumer group without enabling consumption."""
    try:
        redis_client.execute_command(
            "XGROUP CREATE",
            OUTBOX_STREAM,
            EXECUTION_GROUP,
            "$",
            "MKSTREAM",
        )
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise
