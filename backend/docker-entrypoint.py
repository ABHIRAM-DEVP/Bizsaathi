"""Build the container database URL safely and run migrations before the API."""

import os

from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

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


def seed_development_demo_data() -> None:
    from app.core.config import settings

    if settings.ENV != "dev":
        return

    from app.services.demo_seed import seed_demo_data

    engine = create_engine(runtime_database_url, pool_pre_ping=True)
    with Session(engine) as session:
        try:
            seed_result = seed_demo_data(session)
            session.commit()
        except Exception:
            session.rollback()
            raise
    engine.dispose()
    print(
        "Development demo data ready: "
        f"{seed_result['products_created']} products, "
        f"{seed_result['images_created']} photos, "
        f"{seed_result['orders_created']} orders, "
        f"{seed_result['approvals_created']} approvals, "
        f"{seed_result['conversations_available']} synthetic conversations available."
    )


seed_development_demo_data()

os.execvp(
    "uvicorn",
    ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"],
)
