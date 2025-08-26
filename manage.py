# manage.py
from __future__ import annotations

import os
import sys
import click
from alembic import command
from alembic.config import Config
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ALEMBIC_INI = str(ROOT / "alembic.ini")
ALEMBIC_DIR = str(ROOT / "alembic")

def make_config() -> Config:
    cfg = Config(ALEMBIC_INI)
    # url з ENV, щоб працювало в Docker з volumes
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/app")
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", ALEMBIC_DIR)
    return cfg

@click.group()
def cli():
    """FastAPI manage.py — команди міграцій як у Django."""

@cli.command()
@click.option("-m", "--message", default="auto", help="Повідомлення ревізії")
def makemigrations(message: str):
    """Створити ревізію Alembic (аналог Django makemigrations)."""
    cfg = make_config()
    command.revision(cfg, autogenerate=True, message=message)

@cli.command()
@click.argument("target", default="head")
def migrate(target: str):
    """Застосувати міграції до target (аналог Django migrate)."""
    cfg = make_config()
    command.upgrade(cfg, target)

@cli.command()
def show():
    """Показати поточну ревізію."""
    cfg = make_config()
    command.current(cfg)

@cli.command()
def history():
    """Показати історію ревізій."""
    cfg = make_config()
    command.history(cfg)

@cli.command()
@click.argument("rev")
def downgrade(rev: str):
    """Відкотити до ревізії."""
    cfg = make_config()
    command.downgrade(cfg, rev)

if __name__ == "__main__":
    cli()
