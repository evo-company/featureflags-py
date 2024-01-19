from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional, cast

from featureflags_client.http.flags import Flags
from featureflags_client.http.managers.base import (
    AsyncBaseManager,
    BaseManager,
)


class FeatureFlagsClient:
    """
    Feature flags http based client.
    """

    def __init__(self, manager: BaseManager) -> None:
        self._manager = manager

    @contextmanager
    def flags(
        self,
        ctx: Optional[Dict[str, Any]] = None,
        *,
        overrides: Optional[Dict[str, bool]] = None,
    ) -> Generator[Flags, None, None]:
        """
        Context manager to wrap your request handling code and get actual
        flags values.
        """
        yield Flags(self._manager, ctx, overrides)

    def preload(self) -> None:
        """Preload flags from featureflags server.
        This method syncs all flags with server"""
        self._manager.preload()

    async def preload_async(self) -> None:
        """Async version of `preload` method"""

        await cast(AsyncBaseManager, self._manager).preload()
