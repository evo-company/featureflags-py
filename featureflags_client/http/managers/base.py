import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime, timedelta
from enum import EnumMeta
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from featureflags_client.http.constants import Endpoints
from featureflags_client.http.state import HttpState
from featureflags_client.http.types import (
    PreloadFlagsRequest,
    PreloadFlagsResponse,
    SyncFlagsRequest,
    SyncFlagsResponse,
    Variable,
)
from featureflags_client.http.utils import (
    coerce_defaults,
    coerce_values_defaults,
    custom_asdict_factory,
    intervals_gen,
)

log = logging.getLogger(__name__)


def _values_defaults_to_tuple(
    values: List[str], values_defaults: Dict[str, Union[int, str]]
) -> List[Tuple[str, Union[int, str]]]:
    result = []
    for value in values:
        value_default = values_defaults.get(value, "")
        result.append(
            (
                value,
                value_default,
            )
        )
    return result


class BaseManager(ABC):
    """
    Base manager for using with sync http clients.
    """

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: List[Variable],
        defaults: Union[EnumMeta, Type, Dict[str, bool]],
        values_defaults: Optional[
            Union[EnumMeta, Type, Dict[str, Union[int, str]]]
        ] = None,
        request_timeout: int = 5,
        refresh_interval: int = 60,  # 1 minute.
    ) -> None:
        self.url = url
        self.defaults = coerce_defaults(defaults)

        if values_defaults is None:
            values_defaults = {}

        self.values_defaults = coerce_values_defaults(values_defaults)

        self._request_timeout = request_timeout
        self._state = HttpState(
            project=project,
            variables=variables,
            flags=list(self.defaults.keys()),
            values=list(self.values_defaults.keys()),
        )

        self._int_gen = intervals_gen(interval=refresh_interval)
        self._int_gen.send(None)

        self._next_sync = datetime.utcnow()

    @abstractmethod
    def _post(
        self,
        url: Endpoints,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        pass

    def _check_sync(self) -> None:
        if datetime.utcnow() >= self._next_sync:
            try:
                self.sync()
            except Exception as exc:
                self._next_sync = datetime.utcnow() + timedelta(
                    seconds=self._int_gen.send(False)
                )
                log.error(
                    "Failed to exchange: %r, retry after %s",
                    exc,
                    self._next_sync,
                )
            else:
                self._next_sync = datetime.utcnow() + timedelta(
                    seconds=self._int_gen.send(True)
                )
                log.debug(
                    "Exchange complete, next will be after %s",
                    self._next_sync,
                )

    def get_flag(self, name: str) -> Optional[Callable[[Dict], bool]]:
        self._check_sync()
        return self._state.get_flag(name)

    def get_value(
        self, name: str
    ) -> Optional[Callable[[Dict], Union[int, str]]]:
        self._check_sync()
        return self._state.get_value(name)

    def preload(self) -> None:
        payload = PreloadFlagsRequest(
            project=self._state.project,
            variables=self._state.variables,
            flags=self._state.flags,
            values=_values_defaults_to_tuple(
                self._state.values,
                self.values_defaults,
            ),
            version=self._state.version,
        )
        log.debug(
            "Exchange request, project: %s, version: %s, flags: %s, values: %s",
            payload.project,
            payload.version,
            payload.flags,
            payload.values,
        )

        response_raw = self._post(
            url=Endpoints.PRELOAD,
            payload=asdict(payload, dict_factory=custom_asdict_factory),
            timeout=self._request_timeout,
        )
        log.debug("Preload response: %s", response_raw)

        response = PreloadFlagsResponse.from_dict(response_raw)
        self._state.update(response.flags, response.values, response.version)

    def sync(self) -> None:
        payload = SyncFlagsRequest(
            project=self._state.project,
            flags=self._state.flags,
            values=self._state.values,
            version=self._state.version,
        )
        log.debug(
            "Sync request, project: %s, version: %s, flags: %s, values: %s",
            payload.project,
            payload.version,
            payload.flags,
            payload.values,
        )

        response_raw = self._post(
            url=Endpoints.SYNC,
            payload=asdict(payload, dict_factory=custom_asdict_factory),
            timeout=self._request_timeout,
        )
        log.debug("Sync reply: %s", response_raw)

        response = SyncFlagsResponse.from_dict(response_raw)
        self._state.update(response.flags, response.values, response.version)


class AsyncBaseManager(BaseManager):
    """
    Base async manager for using with async http clients.
    """

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: List[Variable],
        defaults: Union[EnumMeta, Type, Dict[str, bool]],
        values_defaults: Optional[
            Union[EnumMeta, Type, Dict[str, Union[int, str]]]
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
        self._refresh_task: Optional[asyncio.Task] = None

    @abstractmethod
    async def _post(  # type: ignore
        self,
        url: Endpoints,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    def get_flag(self, name: str) -> Optional[Callable[[Dict], bool]]:
        return self._state.get_flag(name)

    def get_value(
        self, name: str
    ) -> Optional[Callable[[Dict], Union[int, str]]]:
        return self._state.get_value(name)

    async def preload(self) -> None:  # type: ignore
        """
        Preload flags and values from the server.
        """

        payload = PreloadFlagsRequest(
            project=self._state.project,
            variables=self._state.variables,
            flags=self._state.flags,
            values=_values_defaults_to_tuple(
                self._state.values,
                self.values_defaults,
            ),
            version=self._state.version,
        )
        log.debug(
            "Exchange request, project: %s, version: %s, flags: %s, values: %s",
            payload.project,
            payload.version,
            payload.flags,
            payload.values,
        )

        response_raw = await self._post(
            url=Endpoints.PRELOAD,
            payload=asdict(payload, dict_factory=custom_asdict_factory),
            timeout=self._request_timeout,
        )
        log.debug("Preload response: %s", response_raw)

        response = PreloadFlagsResponse.from_dict(response_raw)
        self._state.update(response.flags, response.values, response.version)

    async def sync(self) -> None:  # type: ignore
        payload = SyncFlagsRequest(
            project=self._state.project,
            flags=self._state.flags,
            values=self._state.values,
            version=self._state.version,
        )
        log.debug(
            "Sync request, project: %s, version: %s, flags: %s, values: %s",
            payload.project,
            payload.version,
            payload.flags,
            payload.values,
        )

        response_raw = await self._post(
            url=Endpoints.SYNC,
            payload=asdict(payload, dict_factory=custom_asdict_factory),
            timeout=self._request_timeout,
        )
        log.debug("Sync reply: %s", response_raw)

        response = SyncFlagsResponse.from_dict(response_raw)
        self._state.update(response.flags, response.values, response.version)

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

        await self.close()

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
