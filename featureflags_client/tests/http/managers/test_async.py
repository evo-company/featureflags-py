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
    TEST_INT_A = 1
    TEST_INT_B = 20


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

    value_test = Value(
        name="TEST",
        enabled=True,
        overridden=True,
        value_default="test",
        value_override="nottest",
        conditions=[value_condition],
    )

    value_test_int_a = Value(
        name="TEST_INT_A",
        enabled=True,
        overridden=True,
        value_default=1,
        value_override=2,
        conditions=[value_condition_int_value],
    )

    value_test_int_b = Value(
        name="TEST_INT_B",
        enabled=False,
        overridden=False,
        value_default=10,
        value_override=10,
        conditions=[],
    )

    mock_preload_response = PreloadFlagsResponse(
        version=1,
        flags=[],
        values=[value_test, value_test_int_a, value_test_int_b],
    )
    with patch.object(manager, "_post") as mock_post:
        mock_post.return_value = mock_preload_response.to_dict()

        await client.preload_async()
        mock_post.assert_called_once()

    # check that resulting values based on conditions
    with client.values({variable.name: check.value}) as values:
        assert values.TEST is value_condition.value_override
        assert values.TEST_INT_A is value_condition_int_value.value_override
        assert values.TEST_INT_B == value_test_int_b.value_default

    # check that resulting values NOT based on conditions
    with client.values({variable.name: f.pystr()}) as values:
        assert values.TEST == value_test.value_override
        assert values.TEST_INT_A == value_test_int_a.value_override
        assert values.TEST_INT_B == value_test_int_b.value_default

    # check that each .values call is isolated
    with client.values({variable.name: check.value}) as values:
        assert values.TEST is value_condition.value_override
        assert values.TEST_INT_A is value_condition_int_value.value_override
        assert values.TEST_INT_B == value_test_int_b.value_default

    # close client connection.
    await manager.close()
