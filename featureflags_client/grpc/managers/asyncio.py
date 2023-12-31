import asyncio
import logging
import warnings
from asyncio import AbstractEventLoop
from typing import Callable, Dict, List, Optional

from featureflags_client.grpc.managers.base import AbstractManager
from featureflags_client.grpc.state import GrpcState
from featureflags_client.grpc.stats_collector import StatsCollector
from featureflags_client.grpc.tracer import Tracer
from featureflags_client.grpc.types import Variable
from featureflags_client.grpc.utils import intervals_gen
from featureflags_protobuf.service_grpc import FeatureFlagsStub
from featureflags_protobuf.service_pb2 import FlagUsage as FlagUsageProto

try:
    import grpclib.client
except ImportError:
    raise ImportError(
        "grpclib is not installed, please install it to use AsyncIOManager "
        "like this `pip install 'featureflags-client[grpclib]'`"
    ) from None

log = logging.getLogger(__name__)


class AsyncIOManager(AbstractManager):
    """Feature flags manager for asyncio apps

    Example:

    .. code-block:: python

        from grpclib.client import Channel

        manager = AsyncIOManager(
            'project.name',
            [],  # variables
            Channel('grpc.featureflags.svc', 50051)
        )
        try:
            await manager.preload(timeout=5)
        except Exception:
            log.exception('Unable to preload feature flags, application will '
                          'start working with defaults and retry later')
        manager.start()
        try:
            pass  # run your application
        finally:
            manager.close()
            await manager.wait_closed()

    :param project: project name
    :param variables: list of :py:class:`~featureflags.client.flags.Variable`
        definitions
    :param channel: instance of :py:class:`grpclib.client.Channel` class,
        pointing to the feature flags gRPC server
    :param loop: asyncio event loop
    """

    _exchange_task = None
    _exchange_timeout = 5

    def __init__(
        self,
        project: str,
        variables: List[Variable],
        channel: grpclib.client.Channel,
        *,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        self._state = GrpcState(project, variables)
        self._channel = channel
        self._loop = loop or asyncio.get_event_loop()

        self._stats = StatsCollector()
        self._stub = FeatureFlagsStub(self._channel)

        self._int_gen = intervals_gen()
        self._int_gen.send(None)

        if loop:
            warnings.warn(
                "The loop arguments is deprecated because it's not necessary.",
                DeprecationWarning,
                stacklevel=2,
            )

    async def preload(
        self,
        *,
        timeout: Optional[int] = None,
        defaults: Optional[Dict] = None,
    ) -> None:
        """
        Preload flags from the server.
        :param timeout: timeout in seconds (for grpclib)
        :param defaults: dict with default values for feature flags.
                         If passed, all feature flags will be synced with
                         server,
                         otherwise flags will be synced only when they are
                         accessed
                         for the first time.
        """
        stats = None
        if defaults is not None:
            stats = self._stats.from_defaults(defaults)

        await self._exchange(timeout, stats)

    def start(self) -> None:
        if self._exchange_task is not None:
            raise RuntimeError("Manager is already started")
        self._exchange_task = self._loop.create_task(self._exchange_coro())

    def close(self) -> None:
        self._exchange_task.cancel()

    async def wait_closed(self) -> None:
        await asyncio.wait([self._exchange_task])
        if self._exchange_task.done():
            try:
                error = self._exchange_task.exception()
            except asyncio.CancelledError:
                pass
            else:
                if error is not None:
                    log.error("Exchange task exited with error: %r", error)

    async def _exchange_coro(self) -> None:
        log.info("Exchange task started")
        while True:
            try:
                await self._exchange(self._exchange_timeout)
                interval = self._int_gen.send(True)
                log.debug("Exchange complete, next will be in %ss", interval)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                log.info("Exchange task exits")
                break
            except Exception as exc:
                interval = self._int_gen.send(False)
                log.error("Failed to exchange: %r, retry in %ss", exc, interval)
                await asyncio.sleep(interval)
                continue

    async def _exchange(
        self,
        timeout: int,
        flags_usage: Optional[List[FlagUsageProto]] = None,
    ) -> None:
        if flags_usage is None:
            flags_usage = self._stats.flush()

        request = self._state.get_request(flags_usage)
        log.debug(
            "Exchange request, project: %r, version: %r, stats: %r",
            request.project,
            request.version,
            request.flags_usage,
        )
        reply = await self._stub.Exchange(request, timeout=timeout)
        log.debug("Exchange reply: %r", reply)
        self._state.apply_reply(reply)

    def get(self, name: str) -> Callable[[Dict], bool] | None:
        return self._state.get(name)

    def add_trace(self, tracer: Tracer) -> None:
        self._stats.update(tracer.interval, tracer.values)
