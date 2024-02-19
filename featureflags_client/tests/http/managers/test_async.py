from unittest.mock import patch

import faker
import pytest

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.aiohttp import AiohttpManager
from featureflags_client.http.managers.httpx import HttpxManager
from featureflags_client.http.types import Flag, PreloadFlagsResponse, Variable

f = faker.Faker()


class Defaults:
    TEST = False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "async_manager_class",
    [
        AiohttpManager,
        HttpxManager,
    ],
)
async def test_manager(async_manager_class, flag, variable, check, condition):
    manager = async_manager_class(
        url="http://flags.server.example",
        project="test",
        variables=[Variable(variable.name, variable.type)],
        defaults=Defaults,
        request_timeout=1,
        refresh_interval=1,
    )
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

        await client.preload_async()
        mock_post.assert_called_once()

    with client.flags({variable.name: check.value}) as flags:
        assert flags.TEST is True

    with client.flags({variable.name: f.pystr()}) as flags:
        assert flags.TEST is False

    with client.flags({variable.name: check.value}) as flags:
        assert flags.TEST is True

    # close client connection.
    await manager.close()
