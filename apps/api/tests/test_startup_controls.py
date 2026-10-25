from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

from app import migrate
from app.database import database_url
from app.redis_streams import execution_consumption_is_disabled


def test_execution_remains_disabled():
    assert execution_consumption_is_disabled() is True


@pytest.mark.parametrize('explicit', [None, '11'])
def test_database_connection_timeout(monkeypatch, explicit):
    url = 'postgresql://localhost/autonomous'
    if explicit:
        url += '?connect_timeout=' + explicit
    monkeypatch.setenv('DATABASE_URL', url)
    assert conninfo_to_dict(database_url())['connect_timeout'] == (explicit or '5')


@pytest.fixture
def migration_database(monkeypatch, tmp_path):
    if not os.getenv('DATABASE_URL'):
        pytest.skip('DATABASE_URL is not configured')
    url = os.environ['DATABASE_URL']
    schema = 'migration_test_' + uuid4().hex
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA {schema}')
        monkeypatch.setenv('DATABASE_URL', make_conninfo(url, options=f'-c search_path={schema}'))
        monkeypatch.setenv('MIGRATIONS_PATH', str(tmp_path))
        try:
            yield tmp_path
        finally:
            conn.execute(f'DROP SCHEMA {schema} CASCADE')


@pytest.mark.integration
def test_concurrent_migration_startup_is_serialized(migration_database):
    (migration_database / '001.sql').write_text(
        'SELECT pg_sleep(0.4); CREATE TABLE startup_probe (id integer);')
    (migration_database / '002.sql').write_text(
        'ALTER TABLE startup_probe ADD COLUMN completed boolean;')
    with ThreadPoolExecutor(max_workers=2) as workers:
        runs = [workers.submit(migrate.main) for _ in range(2)]
        for run in runs:
            run.result(timeout=20)
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        assert conn.execute('SELECT count(*) FROM schema_migrations').fetchone()[0] == 2
        conn.execute('SELECT completed FROM startup_probe')


@pytest.mark.integration
def test_failed_migration_can_be_retried(migration_database):
    (migration_database / '001.sql').write_text('CREATE TABLE startup_probe (id integer);')
    broken = migration_database / '002.sql'
    broken.write_text('CREATE TABLE rolled_back (id integer); SELECT missing_column;')
    with pytest.raises(psycopg.errors.UndefinedColumn):
        migrate.main()
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        assert conn.execute('SELECT version FROM schema_migrations').fetchall() == [('001.sql',)]
        assert conn.execute("SELECT to_regclass('rolled_back')").fetchone()[0] is None
    broken.write_text('CREATE TABLE rolled_back (id integer);')
    migrate.main()
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        assert conn.execute('SELECT count(*) FROM schema_migrations').fetchone()[0] == 2
