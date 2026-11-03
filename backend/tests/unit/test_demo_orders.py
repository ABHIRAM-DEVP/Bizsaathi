from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import InvalidStateError
from app.services.demo_orders import seed_demo_orders


def test_demo_order_seed_refuses_non_development_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENV", "prod")
    session = Mock(spec=Session)

    with pytest.raises(InvalidStateError, match="only be seeded when ENV=dev"):
        seed_demo_orders(session)

    session.execute.assert_not_called()
