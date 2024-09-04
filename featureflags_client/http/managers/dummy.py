import logging
from typing import Any, Callable, Dict, Optional, Union

from featureflags_client.http.constants import Endpoints
from featureflags_client.http.managers.base import (
    AsyncBaseManager,
    BaseManager,
)

log = logging.getLogger(__name__)


class DummyManager(BaseManager):
    """Dummy feature flags manager.

    It can be helpful when you want to use flags with their default values.
    """

    def get(
        self, name: str
    ) -> Optional[Callable[[Dict], Union[bool, int, str]]]:
        """
        So that `featureflags.http.flags.Flags` will use default values.
        """
        return None

    def sync(self) -> None:
        pass

    def preload(self) -> None:
        pass

    def _post(
        self,
        url: Endpoints,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        pass


class AsyncDummyManager(AsyncBaseManager):
    """Dummy feature flags manager for asyncio apps.

    It can be helpful when you want to use flags with their default values.
    """

    def get(
        self, name: str
    ) -> Optional[Callable[[Dict], Union[bool, int, str]]]:
        """
        So that `featureflags.http.flags.Flags` will use default values.
        """
        return None

    async def _post(  # type: ignore
        self,
        url: Endpoints,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        pass

    async def close(self) -> None:
        pass

    async def sync(self) -> None:  # type: ignore
        pass

    async def preload(self) -> None:  # type: ignore
        pass

    def start(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass
