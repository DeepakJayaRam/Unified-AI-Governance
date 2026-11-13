import os
import subprocess
import sys
import sqlite3


def test_fresh_migration_and_roundtrip(tmp_path):
    path = tmp_path / "migration.db"
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + path.as_posix()}
    for command in (["upgrade", "head"], ["downgrade", "base"], ["upgrade", "head"]):
        completed = subprocess.run([sys.executable, "-m", "alembic", *command], env=env, capture_output=True, text=True, timeout=30)
        assert completed.returncode == 0, completed.stdout + completed.stderr
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0001"
        assert db.execute("SELECT name FROM sqlite_master WHERE name='records'").fetchone()
