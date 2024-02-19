from datetime import datetime, timedelta
from unittest.mock import patch

import faker
import pytest

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.requests import RequestsManager
from featureflags_client.http.types import Flag, PreloadFlagsResponse, Variable

f = faker.Faker()


class Defaults:
    TEST = False


@pytest.mark.parametrize(
    "manager_class",
    [
        RequestsManager,
    ],
)
def test_manager(manager_class, flag, variable, check, condition):
    manager = manager_class(
        url="http://flags.server.example",
        project="test",
        variables=[Variable(variable.name, variable.type)],
        defaults=Defaults,
        request_timeout=1,
        refresh_interval=1,
    )

    # Disable auto sync.
    manager._next_sync = datetime.utcnow() + timedelta(hours=1)

    client = FeatureFlagsClient(manager)

    mock_preload_response = PreloadFlagsResponse(
        version=1,
        flags=[
            Flag(
                name="TEST",
                enabled=True,
                overridden=True,
                conditions=[condition],
            ),
        ],
    )
    with patch.object(manager, "_post") as mock_post:
        mock_post.return_value = mock_preload_response.to_dict()

        client.preload()
        mock_post.assert_called_once()

    with client.flags({variable.name: check.value}) as flags:
        assert flags.TEST is True

    with client.flags({variable.name: f.pystr()}) as flags:
        assert flags.TEST is False

    with client.flags({variable.name: check.value}) as flags:
        assert flags.TEST is True
