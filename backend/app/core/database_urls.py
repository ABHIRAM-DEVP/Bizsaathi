"""Database URLs used by the local container entrypoint."""

from collections.abc import Mapping

from sqlalchemy.engine import URL


def build_database_urls(environment: Mapping[str, str]) -> tuple[str, str]:
    def create_url(username: str, password: str) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=username,
            password=password,
            host=environment.get("POSTGRES_HOST", "postgres"),
            port=int(environment.get("POSTGRES_INTERNAL_PORT", "5432")),
            database=environment["POSTGRES_DB"],
        ).render_as_string(hide_password=False)

    runtime_url = create_url(environment["POSTGRES_USER"], environment["POSTGRES_PASSWORD"])
    migration_url = create_url(
        environment.get("MIGRATION_DATABASE_USER", "").strip() or environment["POSTGRES_USER"],
        environment.get("MIGRATION_DATABASE_PASSWORD", "") or environment["POSTGRES_PASSWORD"],
    )
    return runtime_url, migration_url
