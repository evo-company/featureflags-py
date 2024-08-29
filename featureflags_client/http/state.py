from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Union

from featureflags_client.http.conditions import (
    update_flags_state,
    update_values_state,
)
from featureflags_client.http.types import (
    Flag,
    Value,
    Variable,
)


class BaseState(ABC):
    variables: List[Variable]
    flags: List[str]
    values: List[str]
    project: str
    version: int

    _state: Dict[str, Callable[..., Union[bool, int, str]]]

    def __init__(
        self,
        project: str,
        variables: List[Variable],
        flags: List[str],
        values: List[str],
    ) -> None:
        self.project = project
        self.variables = variables
        self.version = 0
        self.flags = flags
        self.values = values

        self._state = {}

    def get(
        self, name: str
    ) -> Optional[Callable[[Dict], Union[bool, int, str]]]:
        return self._state.get(name)

    @abstractmethod
    def update(
        self,
        flags: List[Flag],
        values: List[Value],
        version: int,
    ) -> None:
        pass


class HttpState(BaseState):
    def update(
        self,
        flags: List[Flag],
        values: List[Value],
        version: int,
    ) -> None:
        if self.version != version:
            flags_state = update_flags_state(flags)
            values_state = update_values_state(values)
            self._state = {**flags_state, **values_state}
            self.version = version
