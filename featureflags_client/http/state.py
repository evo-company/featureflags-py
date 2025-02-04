from abc import ABC, abstractmethod
from typing import Callable, Optional, Union

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
    variables: list[Variable]
    flags: list[str]
    values: list[str]
    project: str
    version: int

    _flags_state: dict[str, Callable[..., bool]]
    _values_state: dict[str, Callable[..., Union[int, str]]]

    def __init__(
        self,
        project: str,
        variables: list[Variable],
        flags: list[str],
        values: list[str],
    ) -> None:
        self.project = project
        self.variables = variables
        self.version = 0
        self.flags = flags
        self.values = values

        self._flags_state = {}
        self._values_state = {}

    def get_flag(self, name: str) -> Optional[Callable[[dict], bool]]:
        return self._flags_state.get(name)

    def get_value(
        self, name: str
    ) -> Optional[Callable[[dict], Union[int, str]]]:
        return self._values_state.get(name)

    @abstractmethod
    def update(
        self,
        flags: list[Flag],
        values: list[Value],
        version: int,
    ) -> None:
        pass


class HttpState(BaseState):
    def update(
        self,
        flags: list[Flag],
        values: list[Value],
        version: int,
    ) -> None:
        if self.version != version:
            self._flags_state = update_flags_state(flags)
            self._values_state = update_values_state(values)
            self.version = version
