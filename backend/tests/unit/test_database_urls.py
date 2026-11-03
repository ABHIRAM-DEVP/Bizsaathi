from sqlalchemy.engine import make_url

from app.core.database_urls import build_database_urls


def test_migration_role_can_use_schema_owner_without_changing_runtime_url():
    environment = {
        "POSTGRES_USER": "app_runtime",
        "POSTGRES_PASSWORD": "db-test",
        "POSTGRES_DB": "bizsaathi",
        "MIGRATION_DATABASE_USER": "schema_owner",
    }

    runtime_url, migration_url = build_database_urls(environment)

    assert make_url(runtime_url).username == "app_runtime"
    assert make_url(migration_url).username == "schema_owner"
    assert make_url(migration_url).password == "db-test"


def test_migration_url_defaults_to_runtime_url():
    environment = {
        "POSTGRES_USER": "app_runtime",
        "POSTGRES_PASSWORD": "",
        "POSTGRES_DB": "bizsaathi",
    }

    runtime_url, migration_url = build_database_urls(environment)

    assert migration_url == runtime_url


def test_migration_password_can_differ_from_runtime_password():
    environment = {
        "POSTGRES_USER": "app_runtime",
        "POSTGRES_PASSWORD": "runtime-test",
        "POSTGRES_DB": "bizsaathi",
        "MIGRATION_DATABASE_USER": "schema_owner",
        "MIGRATION_DATABASE_PASSWORD": "owner-test",
    }

    runtime_url, migration_url = build_database_urls(environment)

    assert make_url(runtime_url).password == "runtime-test"
    assert make_url(migration_url).password == "owner-test"
