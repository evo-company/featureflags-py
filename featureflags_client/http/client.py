from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional, Union, cast

from featureflags_client.http.flags import Flags
from featureflags_client.http.managers.base import (
    AsyncBaseManager,
    BaseManager,
)
from featureflags_client.http.values import Values


class FeatureFlagsClient:
    """
    Feature flags and values http based client.
    """

    def __init__(self, manager: BaseManager) -> None:
        self._manager = manager

    @contextmanager
    def flags(
        self,
        ctx: Optional[dict[str, Any]] = None,
        *,
        overrides: Optional[dict[str, bool]] = None,
    ) -> Generator[Flags, None, None]:
        """
        Context manager to wrap your request handling code and get actual
        flags values.
        """
        yield Flags(self._manager, ctx, overrides)

    @contextmanager
    def values(
        self,
        ctx: Optional[dict[str, Any]] = None,
        *,
        overrides: Optional[dict[str, Union[int, str]]] = None,
    ) -> Generator[Values, None, None]:
        """
        Context manager to wrap your request handling code and get actual
        feature values.
        """
        yield Values(self._manager, ctx, overrides)

    def preload(self) -> None:
        """Preload flags and values from featureflags server.
        This method syncs all flags and values with server"""
        self._manager.preload()

    async def preload_async(self) -> None:
        """Async version of `preload` method"""

        await cast(AsyncBaseManager, self._manager).preload()
