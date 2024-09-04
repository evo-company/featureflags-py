import pytest

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.dummy import (
    AsyncDummyManager,
    DummyManager,
)


class Defaults:
    FOO_FEATURE = False
    BAR_FEATURE = True


class ValuesDefaults:
    FOO_FEATURE = "foo"
    BAR_FEATURE = "bar"


def test_sync():
    manager = DummyManager(
        url="",
        project="test",
        variables=[],
        defaults=Defaults,
        request_timeout=1,
        refresh_interval=1,
    )
    client = FeatureFlagsClient(manager)

    with client.flags() as flags:
        assert flags.FOO_FEATURE is False
        assert flags.BAR_FEATURE is True


@pytest.mark.asyncio
async def test_async():
    manager = AsyncDummyManager(
        url="",
        project="test",
        variables=[],
        defaults=Defaults,
        request_timeout=1,
        refresh_interval=1,
    )
    client = FeatureFlagsClient(manager)

    await client.preload_async()

    manager.start()

    with client.flags() as flags:
        assert flags.FOO_FEATURE is False
        assert flags.BAR_FEATURE is True

    await manager.wait_closed()


def test_values_sync():
    manager = DummyManager(
        url="",
        project="test",
        variables=[],
        defaults={},
        values_defaults=ValuesDefaults,
        request_timeout=1,
        refresh_interval=1,
    )
    client = FeatureFlagsClient(manager)

    with client.values() as values:
        assert values.FOO_FEATURE == "foo"
        assert values.BAR_FEATURE == "bar"


@pytest.mark.asyncio
async def test_values_async():
    manager = AsyncDummyManager(
        url="",
        project="test",
        variables=[],
        defaults={},
        values_defaults=ValuesDefaults,
        request_timeout=1,
        refresh_interval=1,
    )
    client = FeatureFlagsClient(manager)

    await client.preload_async()

    manager.start()

    with client.values() as values:
        assert values.FOO_FEATURE == "foo"
        assert values.BAR_FEATURE == "bar"

    await manager.wait_closed()
