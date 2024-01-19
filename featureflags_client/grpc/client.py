import inspect
from collections.abc import Mapping
from contextlib import contextmanager
from enum import EnumMeta
from typing import Any, Dict, Generator, Optional, Union

from featureflags_client.grpc.flags import Flags
from featureflags_client.grpc.managers.base import AbstractManager


class FeatureFlagsClient:
    """Feature flags client

    :param defaults: flags are defined together with their default values,
        defaults can be provided as dict or class object with attributes
    :param manager: flags manager
    """

    def __init__(
        self,
        defaults: Union[EnumMeta, type, Dict[str, bool]],
        manager: AbstractManager,
    ) -> None:
        if isinstance(defaults, EnumMeta):  # deprecated
            defaults = {  # type: ignore
                k: v.value for k, v in defaults.__members__.items()
            }
        elif inspect.isclass(defaults):
            defaults = {
                k: getattr(defaults, k)
                for k in dir(defaults)
                if k.isupper() and not k.startswith("_")
            }
        elif not isinstance(defaults, Mapping):
            raise TypeError(f"Invalid defaults type: {type(defaults)!r}")

        invalid = [
            k
            for k, v in defaults.items()
            if not isinstance(k, str) or not isinstance(v, bool)
        ]
        if invalid:
            raise TypeError(
                "Invalid flag definition: {}".format(
                    ", ".join(map(repr, invalid))
                )
            )

        self._defaults = defaults
        self._manager = manager

    @contextmanager
    def flags(
        self,
        ctx: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, bool]] = None,
    ) -> Generator[Flags, None, None]:
        """Context manager to wrap your request handling code and get actual
        flags values

        Example:

        .. code-block:: python

            with client.flags() as flags:
                print(flags.FOO_FEATURE)

        :param ctx: current variable values
        :param overrides: flags to override
        :return: :py:class:`Flags` object
        """
        flags = None
        try:
            flags = Flags(
                self._defaults,
                self._manager,
                ctx,
                overrides,
            )
            yield flags
        finally:
            if flags is not None:
                flags.add_trace()

    def preload(self, timeout: Optional[int] = None) -> None:
        """Preload flags from featureflags.server.
        This method syncs all flags with server"""
        self._manager.preload(timeout=timeout, defaults=self._defaults)

    async def preload_async(self, timeout: Optional[int] = None) -> None:
        """Async version of `preload` method"""
        await self._manager.preload(  # type: ignore
            timeout=timeout,
            defaults=self._defaults,
        )
