import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for persistent operations")
    parameters = conninfo_to_dict(url)
    parameters.setdefault("connect_timeout", "5")
    return make_conninfo(**parameters)


@contextmanager
def transaction() -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url()) as conn:
        with conn.transaction():
            yield conn
