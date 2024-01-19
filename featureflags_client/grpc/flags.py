from typing import Any, Dict, List, Optional, Tuple

from featureflags_client.grpc.managers.base import AbstractManager
from featureflags_client.grpc.tracer import Tracer


class Flags:
    """Flags object to access current flags' state

    Flag values on this object can't change. So even if flag's state is changed
    during request, your application will see the same value, and only for next
    requests your application will see new value.

    This object is returned from :py:meth:`Client.flags` context manager. No
    need to instantiate it directly.
    """

    def __init__(
        self,
        defaults: Dict[str, bool],
        manager: AbstractManager,
        ctx: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, bool]] = None,
    ) -> None:
        self._defaults = defaults
        self._manager = manager
        self._tracer = Tracer()
        self._ctx = ctx or {}
        self._overrides = overrides or {}

    def __getattr__(self, name: str) -> bool:
        try:
            default = self._defaults[name]
        except KeyError as exc:
            raise AttributeError(f"Flag {name} is not defined") from exc

        try:
            value = self._overrides[name]
        except KeyError:
            check = self._manager.get(name)
            value = check(self._ctx) if check is not None else default

        self._tracer.inc(name, value)
        # caching/snapshotting
        setattr(self, name, value)
        return value

    def __history__(self) -> List[Tuple[str, bool]]:
        """Returns an ordered history for flags that were checked"""
        return list(self._tracer.values.items())  # type: ignore

    def add_trace(self) -> None:
        self._manager.add_trace(self._tracer)
