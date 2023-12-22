from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Dict, Optional

if TYPE_CHECKING:
    from featureflags.grpc.flags import Tracer


class AbstractManager(ABC):
    @abstractmethod
    def get(self, name: str) -> Callable[[Dict], bool] | None:
        pass

    @abstractmethod
    def add_trace(self, tracer: Optional["Tracer"]) -> None:
        pass
