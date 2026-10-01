import re

import pytest


def pytest_collection_modifyitems(config, items):
    if re.search(r"\bintegration\b", config.getoption("markexpr")):
        return

    skip_integration = pytest.mark.skip(
        reason=(
            "Requires live LOCAL PostgreSQL, Redis, and Kafka; "
            "run pytest -m integration to enable."
        )
    )
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip_integration)
