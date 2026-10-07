import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for persistent operations")
    return url


@contextmanager
def transaction() -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url()) as conn:
        with conn.transaction():
            yield conn
