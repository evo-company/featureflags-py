from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from featureflags_protobuf import service_pb2
from featureflags_protobuf.service_pb2 import FlagUsage as FlagUsageProto
from hiku.builder import Q, build
from hiku.export.protobuf import export
from hiku.query import Node as QueryNode

from featureflags_client.grpc.conditions import load_flags
from featureflags_client.grpc.types import Variable


def get_grpc_graph_query(project_name: str) -> QueryNode:
    return export(
        build(
            [
                Q.flags(project_name=project_name)[
                    Q.id,
                    Q.name,
                    Q.enabled,
                    Q.overridden,
                    Q.conditions[
                        Q.id,
                        Q.checks[
                            Q.id,
                            Q.variable[
                                Q.id,
                                Q.name,
                                Q.type,
                            ],
                            Q.operator,
                            Q.value_string,
                            Q.value_number,
                            Q.value_timestamp,
                            Q.value_set,
                        ],
                    ],
                ],
            ]
        )
    )


class BaseState(ABC):
    variables: List[Variable]
    project: str
    version: int

    _state: Dict[str, Callable[[Dict], bool]]

    def __init__(self, project: str, variables: List[Variable]) -> None:
        self.project = project
        self.variables = variables
        self.version = 0

        self._state = {}

    def get(self, flag_name: str) -> Optional[Callable[[Dict], bool]]:
        return self._state.get(flag_name)

    @abstractmethod
    def get_request(self, flags_usage: List[FlagUsageProto]) -> Any:
        pass

    @abstractmethod
    def apply_reply(self, reply: Any) -> None:
        pass


class GrpcState(BaseState):
    def __init__(self, project: str, variables: List[Variable]) -> None:
        super().__init__(project, variables)
        self._variables_sent = False
        self._exchange_query = get_grpc_graph_query(project)

    def get_request(
        self, flags_usage: List[FlagUsageProto]
    ) -> service_pb2.ExchangeRequest:
        request = service_pb2.ExchangeRequest(
            project=self.project,
            version=self.version,
        )
        request.query.CopyFrom(self._exchange_query)

        if not self._variables_sent:
            for var in self.variables:
                request.variables.add(name=var.name, type=var.type)

        request.flags_usage.extend(flags_usage)
        return request

    def apply_reply(self, reply: service_pb2.ExchangeReply) -> None:
        self._variables_sent = True
        if self.version != reply.version:
            self._state = load_flags(reply.result)
            self.version = reply.version
