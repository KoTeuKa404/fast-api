# alembic/env.py
from logging.config import fileConfig
import os
import sys
from pathlib import Path

# >>> додано: гарантуємо, що /app у PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]  # /app
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, pool
from alembic import context

# Імпортуємо метадані моделей
from app.db import Base
from app import models  # noqa: F401

config = context.config

# логування alembic.ini, якщо є
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL беремо з env або з ini
DB_URL = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
if not DB_URL:
    raise RuntimeError("DATABASE_URL не заданий і sqlalchemy.url відсутній у alembic.ini")

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DB_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
