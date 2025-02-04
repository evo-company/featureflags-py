import logging
from enum import EnumMeta
from typing import Any, Optional, Union

from featureflags_client.http.constants import Endpoints
from featureflags_client.http.managers.base import (
    AsyncBaseManager,
)
from featureflags_client.http.types import (
    Variable,
)

try:
    import httpx
except ImportError:
    raise ImportError(
        "`httpx` is not installed, please install it to use HttpxManager "
        "like this `pip install 'featureflags-client[httpx]'`"
    ) from None

log = logging.getLogger(__name__)


class HttpxManager(AsyncBaseManager):
    """Feature flags manager for asyncio apps with `httpx` client."""

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: list[Variable],
        defaults: Union[EnumMeta, type, dict[str, bool]],
        values_defaults: Optional[
            Union[EnumMeta, type, dict[str, Union[int, str]]]
        ] = None,
        request_timeout: int = 5,
        refresh_interval: int = 10,
    ) -> None:
        super().__init__(
            url,
            project,
            variables,
            defaults,
            values_defaults,
            request_timeout,
            refresh_interval,
        )
        self._session = httpx.AsyncClient(base_url=url)

    async def close(self) -> None:
        await self._session.aclose()

    async def _post(  # type: ignore
        self,
        url: Endpoints,
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        response = await self._session.post(
            url=httpx.URL(url.value),
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data
