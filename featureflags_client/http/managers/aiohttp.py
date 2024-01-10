import logging
from enum import EnumMeta
from typing import Any, Dict, List, Mapping, Type, Union

from featureflags_client.http.constants import Endpoints
from featureflags_client.http.managers.base import (
    AsyncBaseManager,
)
from featureflags_client.http.types import (
    Variable,
)

try:
    import aiohttp
except ImportError:
    raise ImportError(
        "`aiohttp` is not installed, please install it to use AiohttpManager "
        "like this `pip install 'featureflags-client[aiohttp]'`"
    ) from None

log = logging.getLogger(__name__)


class AiohttpManager(AsyncBaseManager):
    """Feature flags manager for asyncio apps with `aiohttp` client."""

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: List[Variable],
        defaults: Union[EnumMeta, Type, Mapping[str, bool]],
        request_timeout: int = 5,
        refresh_interval: int = 10,
    ) -> None:
        super().__init__(
            url,
            project,
            variables,
            defaults,
            request_timeout,
            refresh_interval,
        )
        self._session = aiohttp.ClientSession(base_url=url)

    async def close_client(self) -> None:
        await self._session.close()

    async def _post(
        self,
        url: Endpoints,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        async with self._session.post(
            url=url.value,
            json=payload,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            response_data = await response.json()

        return response_data
