from typing import Any, Dict, Optional, Union

from featureflags_client.http.managers.base import BaseManager


class Values:
    """
    Values object to access current feature values state.
    """

    def __init__(
        self,
        manager: BaseManager,
        ctx: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Union[int, str]]] = None,
    ) -> None:
        self._manager = manager
        self._defaults = manager.values_defaults
        self._ctx = ctx or {}
        self._overrides = overrides or {}

    def __getattr__(self, name: str) -> Union[int, str]:
        default = self._defaults.get(name)
        if default is None:
            raise AttributeError(f"Feature value is not defined: {name}")

        value = self._overrides.get(name)
        if value is None:
            check = self._manager.get_value(name)
            value = check(self._ctx) if check is not None else default

        # caching/snapshotting
        setattr(self, name, value)
        return value
