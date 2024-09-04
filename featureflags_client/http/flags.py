from typing import Any, Dict, Optional

from featureflags_client.http.managers.base import BaseManager


class Flags:
    """
    Flags object to access current flags state.
    """

    def __init__(
        self,
        manager: BaseManager,
        ctx: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, bool]] = None,
    ) -> None:
        self._manager = manager
        self._defaults = manager.defaults
        self._ctx = ctx or {}
        self._overrides = overrides or {}

    def __getattr__(self, name: str) -> bool:
        default = self._defaults.get(name)
        if default is None:
            raise AttributeError(f"Flag is not defined: {name}")

        value = self._overrides.get(name)
        if value is None:
            check = self._manager.get_flag(name)
            value = check(self._ctx) if check is not None else default

        # caching/snapshotting
        setattr(self, name, value)
        return value
