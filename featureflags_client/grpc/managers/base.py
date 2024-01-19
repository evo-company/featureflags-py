from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Dict, Optional

if TYPE_CHECKING:
    from featureflags_client.grpc.flags import Tracer


class AbstractManager(ABC):
    @abstractmethod
    def get(self, name: str) -> Optional[Callable[[Dict], bool]]:
        pass

    @abstractmethod
    def add_trace(self, tracer: Optional["Tracer"]) -> None:
        pass

    @abstractmethod
    def preload(
        self,
        timeout: Optional[int] = None,
        defaults: Optional[Dict] = None,
    ) -> None:
        pass
