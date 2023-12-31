from contextlib import contextmanager
from typing import Any, Dict, Optional, cast

from featureflags_client.http.flags import Flags
from featureflags_client.http.managers.base import (
    AbstractManager,
    AsyncAbstractManager,
)


class FeatureFlagsClient:
    """
    Feature flags http based client.
    """

    def __init__(self, manager: AbstractManager) -> None:
        self._manager = manager

    @contextmanager
    def flags(
        self,
        ctx: Optional[Dict[str, Any]] = None,
        *,
        overrides: Optional[Dict[str, bool]] = None,
    ) -> Flags:
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

        await cast(AsyncAbstractManager, self._manager).preload()
