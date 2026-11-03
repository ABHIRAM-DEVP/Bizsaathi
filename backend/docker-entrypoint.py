"""Build the container database URL safely and run migrations before the API."""

import os

from alembic.config import Config

from alembic import command
from app.core.database_urls import build_database_urls

runtime_database_url, migration_database_url = build_database_urls(os.environ)
os.environ.pop("MIGRATION_DATABASE_USER", None)
os.environ.pop("MIGRATION_DATABASE_PASSWORD", None)
os.environ["DATABASE_URL"] = migration_database_url

alembic_config = Config()
alembic_config.set_main_option("script_location", "/app/alembic")
command.upgrade(alembic_config, "head")
os.environ["DATABASE_URL"] = runtime_database_url
os.execvp(
    "uvicorn",
    ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"],
)
