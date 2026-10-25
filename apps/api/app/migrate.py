import os
from pathlib import Path

import psycopg

from .database import database_url


# One session lock per database; acquired before even creating schema_migrations.
MIGRATION_LOCK_ID = 7634102501


def main() -> None:
    migrations_path = Path(os.getenv("MIGRATIONS_PATH", "/migrations"))
    migrations = sorted(migrations_path.glob("*.sql"))
    if not migrations:
        raise RuntimeError(f"No SQL migrations found in {migrations_path}")

    # Explicit transactions commit each version and its ledger entry together.
    # Closing the session releases the advisory lock on both success and error.
    with psycopg.connect(database_url(), autocommit=True) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            for migration in migrations:
                with conn.transaction():
                    applied = conn.execute(
                        "SELECT 1 FROM schema_migrations WHERE version = %s",
                        (migration.name,),
                    ).fetchone()
                    if applied:
                        continue
                    conn.execute(migration.read_text(encoding="utf-8"))
                    conn.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (migration.name,),
                    )
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))

    print(f"Applied migrations from {migrations_path}")


if __name__ == "__main__":
    main()
