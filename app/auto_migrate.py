from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

log = logging.getLogger("app.migrate")

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/app")
ALEMBIC_INI = os.getenv("ALEMBIC_INI", os.path.abspath("alembic.ini"))
ALEMBIC_SCRIPT_LOCATION = os.getenv("ALEMBIC_SCRIPT_LOCATION", os.path.abspath("alembic"))
LOCK_KEY = int(os.getenv("MIGRATION_LOCK_KEY", "424242"))  # будь-яке фіксоване число


def _mask_dsn(dsn: str) -> str:
    try:
        return dsn.replace("postgres:postgres", "postgres:***")
    except Exception:
        return dsn


def _wait_db(max_wait_sec: int = 30) -> bool:
    """Чекаємо БД до max_wait_sec. Повертає True якщо ОК, False якщо ні."""
    start = time.time()
    while time.time() - start < max_wait_sec:
        try:
            eng = create_engine(DB_URL, pool_pre_ping=True, future=True)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("DB is up")
            return True
        except Exception as e:
            log.info("Waiting for DB... %s", getattr(e, "args", e))
            time.sleep(1)
    log.error("DB is not available after %ss", max_wait_sec)
    return False


def _upgrade_head() -> None:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", ALEMBIC_SCRIPT_LOCATION)
    cfg.set_main_option("sqlalchemy.url", DB_URL)
    log.info("Running alembic upgrade head (DB=%s)", _mask_dsn(DB_URL))
    command.upgrade(cfg, "head")
    log.info("Alembic applied successfully")


def run_automigrate_if_enabled() -> None:
    """Запускає alembic upgrade head один раз; ніколи не кидає виняток нагору."""
    try:
        if os.getenv("AUTO_MIGRATE", "1").lower() not in {"1", "true", "yes", "on"}:
            log.info("AUTO_MIGRATE disabled; skipping migrations")
            return

        log.info(
            "Auto-migrate: start (DB=%s, ini=%s, scripts=%s)",
            _mask_dsn(DB_URL),
            ALEMBIC_INI,
            ALEMBIC_SCRIPT_LOCATION,
        )

        if not _wait_db(max_wait_sec=30):
            log.error("Auto-migrate: DB not ready, skipping")
            return

        # SQLite – без advisory lock
        if DB_URL.startswith("sqlite"):
            _upgrade_head()
            return

        eng = create_engine(DB_URL, pool_pre_ping=True, future=True)
        with eng.begin() as conn:
            # лише один процес виконає міграції
            got_lock = conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar()
            if not got_lock:
                log.info("Another process is running migrations — skipping in this worker")
                return

            try:
                _upgrade_head()
            finally:
                conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})

        log.info("Auto-migrate: done")

    except Exception as e:
        # Критично: ніколи не валимо воркер — лише логуємо
        log.exception("Auto-migrate failed (ignored): %s", e)
        return
