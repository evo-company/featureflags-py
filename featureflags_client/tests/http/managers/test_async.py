from unittest.mock import patch

import faker
import pytest

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.aiohttp import AiohttpManager
from featureflags_client.http.managers.httpx import HttpxManager
from featureflags_client.http.types import (
    Flag,
    PreloadFlagsResponse,
    Value,
    Variable,
)

f = faker.Faker()


class Defaults:
    TEST = False


class ValuesDefaults:
    TEST = "test"
    TEST_INT = 1


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
        values=[],
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "async_manager_class",
    [
        AiohttpManager,
        HttpxManager,
    ],
)
async def test_values_manager(
    async_manager_class,
    value,
    variable,
    check,
    value_condition,
    value_condition_int_value,
):
    manager = async_manager_class(
        url="http://flags.server.example",
        project="test",
        variables=[Variable(variable.name, variable.type)],
        defaults={},
        values_defaults=ValuesDefaults,
        request_timeout=1,
        refresh_interval=1,
    )
    client = FeatureFlagsClient(manager)

    mock_preload_response = PreloadFlagsResponse(
        version=1,
        flags=[],
        values=[
            Value(
                name="TEST",
                enabled=True,
                overridden=True,
                value_default="test",
                value_override="nottest",
                conditions=[value_condition],
            ),
            Value(
                name="TEST_INT",
                enabled=True,
                overridden=True,
                value_default=1,
                value_override=2,
                conditions=[value_condition_int_value],
            ),
        ],
    )
    with patch.object(manager, "_post") as mock_post:
        mock_post.return_value = mock_preload_response.to_dict()

        await client.preload_async()
        mock_post.assert_called_once()

    with client.values({variable.name: check.value}) as values:
        assert values.TEST is value_condition.value_override
        assert values.TEST_INT is value_condition_int_value.value_override

    with client.values({variable.name: f.pystr()}) as values:
        assert values.TEST == "nottest"
        assert values.TEST_INT == 2

    with client.values({variable.name: check.value}) as values:
        assert values.TEST is value_condition.value_override
        assert values.TEST_INT is value_condition_int_value.value_override

    # close client connection.
    await manager.close()
