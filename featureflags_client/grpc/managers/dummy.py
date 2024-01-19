from typing import Callable, Dict, Optional

from featureflags_client.grpc.managers.base import AbstractManager
from featureflags_client.grpc.tracer import Tracer


class DummyManager(AbstractManager):
    """Dummy feature flags manager

    It can be helpful when you want to use flags with their default values.

    Example:

    .. code-block:: python

        class Defaults:
            FOO_FEATURE = False

        client = Client(Defaults, DummyManager())

        with client.flags() as flags:
            assert flags.FOO_FEATURE is False

    """

    def preload(
        self,
        timeout: Optional[int] = None,
        defaults: Optional[Dict] = None,
    ) -> None:
        pass

    def get(self, name: str) -> Optional[Callable[[Dict], bool]]:
        return None

    def add_trace(self, tracer: Optional[Tracer]) -> None:
        pass
