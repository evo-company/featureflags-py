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

    _flags_state: Dict[str, Callable[..., bool]]
    _values_state: Dict[str, Callable[..., Union[int, str]]]

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

        self._flags_state = {}
        self._values_state = {}

    def get_flag(self, name: str) -> Optional[Callable[[Dict], bool]]:
        return self._flags_state.get(name)

    def get_value(
        self, name: str
    ) -> Optional[Callable[[Dict], Union[int, str]]]:
        return self._values_state.get(name)

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
            self._flags_state = update_flags_state(flags)
            self._values_state = update_values_state(values)
            self.version = version
