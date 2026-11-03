"""Seed synthetic order examples in the local development database."""

from app.core.config import settings
from app.models.base import get_session
from app.services.demo_orders import seed_demo_orders


def main() -> None:
    if settings.ENV != "dev":
        raise SystemExit("Refusing to seed demo orders unless ENV=dev.")

    session = get_session()
    try:
        result = seed_demo_orders(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print(
        "Demo order seed complete: "
        f"{result['orders_created']} orders and {result['approvals_created']} pending approval(s) created."
    )


if __name__ == "__main__":
    main()
