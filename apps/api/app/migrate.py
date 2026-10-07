import os
from pathlib import Path

import psycopg


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    migrations_path = Path(os.getenv("MIGRATIONS_PATH", "/migrations"))
    migrations = sorted(migrations_path.glob("*.sql"))

    with psycopg.connect(database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()

        for migration in migrations:
            applied = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s",
                (migration.name,),
            ).fetchone()
            if applied:
                continue

            sql = migration.read_text(encoding="utf-8")
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (migration.name,),
                )

    print(f"Applied migrations from {migrations_path}")


if __name__ == "__main__":
    main()
