from abc import ABC, abstractmethod
from enum import EnumMeta
from typing import Callable, Dict, List, Mapping, Optional, Type, Union

from featureflags.grpc.utils import intervals_gen
from featureflags.http.state import HttpState
from featureflags.http.types import Variable
from featureflags.http.utils import coerce_defaults


class AbstractManager(ABC):
    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: List[Variable],
        defaults: Union[EnumMeta, Type, Mapping[str, bool]],
        request_timeout: int = 5,
        refresh_interval: int = 60,  # 1 minute.
    ) -> None:
        self.url = url
        self.defaults = coerce_defaults(defaults)

        self._refresh_interval = refresh_interval
        self._request_timeout = request_timeout

        self._state = HttpState(
            project=project,
            variables=variables,
            flags=list(self.defaults.keys()),
        )

        self._int_gen = intervals_gen(interval=self._refresh_interval)
        self._int_gen.send(None)

    @abstractmethod
    def get(self, name: str) -> Optional[Callable[[Dict], bool]]:
        pass

    @abstractmethod
    def preload(self) -> None:
        pass


class AsyncAbstractManager(AbstractManager):
    @abstractmethod
    async def preload(self) -> None:
        pass
