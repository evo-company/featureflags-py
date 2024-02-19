import pytest

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.dummy import (
    AsyncDummyManager,
    DummyManager,
)


class Defaults:
    FOO_FEATURE = False
    BAR_FEATURE = True


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
