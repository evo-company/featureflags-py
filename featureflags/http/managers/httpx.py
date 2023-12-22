import asyncio
import logging
from dataclasses import asdict
from enum import EnumMeta
from typing import Any, Callable, Dict, List, Mapping, Optional, Type, Union

from featureflags.http.constants import Endpoints
from featureflags.http.managers.base import (
    AsyncAbstractManager,
)
from featureflags.http.types import (
    PreloadFlagsRequest,
    PreloadFlagsResponse,
    SyncFlagsRequest,
    SyncFlagsResponse,
    Variable,
)
from featureflags.http.utils import custom_asdict_factory

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx is not installed, please install it to use AsyncHttpManager "
        "like this `pip install 'featureflags-client[httpx]'`"
    ) from None

log = logging.getLogger(__name__)


class AsyncHttpManager(AsyncAbstractManager):
    """Feature flags manager for asyncio apps with `httpx` client."""

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: List[Variable],
        defaults: Union[EnumMeta, Type, Mapping[str, bool]],
        *,
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

        self._session = httpx.AsyncClient(base_url=url)
        self._refresh_task: Optional[asyncio.Task] = None

    async def preload(self) -> None:
        """
        Preload flags from the server.
        """

        payload = PreloadFlagsRequest(
            project=self._state.project,
            variables=self._state.variables,
            flags=self._state.flags,
            version=self._state.version,
        )
        log.debug(
            "Exchange request, project: %s, version: %s, flags: %s",
            payload.project,
            payload.version,
            payload.flags,
        )

        response_raw = await self._post(
            url=httpx.URL(Endpoints.PRELOAD.value),
            payload=asdict(payload, dict_factory=custom_asdict_factory),
            timeout=self._request_timeout,
        )
        log.debug("Preload response: %s", response_raw)

        response = PreloadFlagsResponse.from_dict(response_raw)
        self._state.update(response.flags, response.version)

    async def sync(self) -> None:
        payload = SyncFlagsRequest(
            project=self._state.project,
            flags=self._state.flags,
            version=self._state.version,
        )
        log.debug(
            "Sync request, project: %s, version: %s, flags: %s",
            payload.project,
            payload.version,
            payload.flags,
        )

        response_raw = await self._post(
            url=httpx.URL(Endpoints.SYNC.value),
            payload=asdict(payload, dict_factory=custom_asdict_factory),
            timeout=self._request_timeout,
        )
        log.debug("Sync reply: %s", response_raw)

        response = SyncFlagsResponse.from_dict(response_raw)
        self._state.update(response.flags, response.version)

    def get(self, name: str) -> Callable[[Dict], bool] | None:
        return self._state.get(name)

    def start(self) -> None:
        if self._refresh_task is not None:
            raise RuntimeError("Manager is already started")

        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def wait_closed(self) -> None:
        self._refresh_task.cancel()
        await asyncio.wait([self._refresh_task])

        if self._refresh_task.done():
            try:
                error = self._refresh_task.exception()
            except asyncio.CancelledError:
                pass
            else:
                if error is not None:
                    log.error("Flags refresh task exited with error: %r", error)

        await self._session.aclose()

    async def _post(
        self,
        url: httpx.URL,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        response = await self._session.post(
            url=url,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data

    async def _refresh_loop(self) -> None:
        log.info("Flags refresh task started")

        while True:
            try:
                await self.sync()
                interval = self._int_gen.send(True)
                log.debug(
                    "Flags refresh complete, next will be in %ss",
                    interval,
                )
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                log.info("Flags refresh task already exits")
                break
            except Exception as exc:
                interval = self._int_gen.send(False)
                log.error(
                    "Failed to refresh flags: %s, retry in %ss", exc, interval
                )
                await asyncio.sleep(interval)
