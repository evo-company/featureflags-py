from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from featureflags_client.http.conditions import update_flags_state
from featureflags_client.http.types import (
    Flag,
    Variable,
)


class BaseState(ABC):
    variables: List[Variable]
    flags: List[str]
    project: str
    version: int

    _state: Dict[str, Callable[..., bool]]

    def __init__(
        self,
        project: str,
        variables: List[Variable],
        flags: List[str],
    ) -> None:
        self.project = project
        self.variables = variables
        self.version = 0
        self.flags = flags

        self._state = {}

    def get(self, flag_name: str) -> Optional[Callable[[Dict], bool]]:
        return self._state.get(flag_name)

    @abstractmethod
    def update(self, flags: List[Flag], version: int) -> None:
        pass


class HttpState(BaseState):
    def update(
        self,
        flags: List[Flag],
        version: int,
    ) -> None:
        if self.version != version:
            self._state = update_flags_state(flags)
            self.version = version
