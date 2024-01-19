import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from featureflags_protobuf.service_pb2 import FlagUsage as FlagUsageProto
from featureflags_protobuf.service_pb2_grpc import FeatureFlagsStub

from featureflags_client.grpc.managers.base import AbstractManager
from featureflags_client.grpc.state import GrpcState
from featureflags_client.grpc.stats_collector import StatsCollector
from featureflags_client.grpc.tracer import Tracer
from featureflags_client.grpc.types import Variable
from featureflags_client.grpc.utils import intervals_gen

try:
    import grpc
except ImportError:
    raise ImportError(
        "grpcio is not installed, please install it to use SyncManager "
        "like this `pip install 'featureflags-client[grpcio]'`"
    ) from None

log = logging.getLogger(__name__)


class SyncManager(AbstractManager):
    """Feature flags manager for synchronous apps

    Example:

    .. code-block:: python

        from grpc import insecure_channel

        manager = SyncManager(
            'project.name',
            [],  # variables
            insecure_channel('grpc.featureflags.svc:50051'),
        )

    :param project: project name
    :param variables: list of :py:class:`~featureflags.client.flags.Variable`
        definitions
    :param channel: instance of :py:class:`grpc.Channel` class, pointing to the
        feature flags gRPC server
    """

    _exchange_timeout = 5

    def __init__(
        self, project: str, variables: List[Variable], channel: grpc.Channel
    ) -> None:
        self._state = GrpcState(project, variables)
        self._channel = channel

        self._stats = StatsCollector()
        self._stub = FeatureFlagsStub(channel)

        self._int_gen = intervals_gen()
        self._int_gen.send(None)
        self._next_exchange = datetime.utcnow()

    def preload(
        self,
        timeout: Optional[int] = None,
        defaults: Optional[Dict] = None,
    ) -> None:
        """
        Preload flags from the server.
        :param timeout: timeout in seconds (for grpcio)
        :param defaults: dict with default values for feature flags.
                         If passed, all feature flags will be synced with
                         server,
                         otherwise flags will be synced only when they are
                         accessed
                         for the first time.
        """
        flags_usage = (
            None if defaults is None else self._stats.from_defaults(defaults)
        )
        self._exchange(timeout, flags_usage)

    def _exchange(
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
        reply = self._stub.Exchange(request, timeout=timeout)
        log.debug("Exchange reply: %r", reply)
        self._state.apply_reply(reply)

    def get(self, name: str) -> Optional[Callable[[Dict], bool]]:
        if datetime.utcnow() >= self._next_exchange:
            try:
                self._exchange(self._exchange_timeout)
            except Exception as exc:
                self._next_exchange = datetime.utcnow() + timedelta(
                    seconds=self._int_gen.send(False)
                )
                log.error(
                    "Failed to exchange: %r, retry after %s",
                    exc,
                    self._next_exchange,
                )
            else:
                self._next_exchange = datetime.utcnow() + timedelta(
                    seconds=self._int_gen.send(True)
                )
                log.debug(
                    "Exchange complete, next will be after %s",
                    self._next_exchange,
                )
        return self._state.get(name)

    def add_trace(self, tracer: Optional[Tracer]) -> None:
        self._stats.update(tracer.interval, tracer.values)
