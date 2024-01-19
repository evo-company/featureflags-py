from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from typing import DefaultDict, Dict, List

from featureflags_protobuf.service_pb2 import FlagUsage as FlagUsageProto
from google.protobuf.timestamp_pb2 import Timestamp as TimestampProto


class StatsCollector:
    """
    Accumulates interval/flag/requests count
    """

    def __init__(self) -> None:
        self._acc: DefaultDict = defaultdict(
            lambda: defaultdict(lambda: [0, 0])
        )

    def update(
        self,
        interval: datetime,
        values: OrderedDict,
    ) -> None:
        for name, value in values.items():
            self._acc[interval][name][bool(value)] += 1

    def flush(
        self,
        delta: timedelta = timedelta(minutes=1),
    ) -> List[FlagUsageProto]:
        now = datetime.utcnow()
        to_flush = [i for i in self._acc if now - i > delta]
        stats = []
        for interval in to_flush:
            acc = self._acc.pop(interval)
            for flag_name, (neg_count, pos_count) in acc.items():
                interval_pb = TimestampProto()
                interval_pb.FromDatetime(interval)
                stats.append(
                    FlagUsageProto(  # type: ignore
                        name=flag_name,
                        interval=interval_pb,
                        negative_count=neg_count,
                        positive_count=pos_count,
                    )
                )
        return stats

    @staticmethod
    def from_defaults(defaults: Dict) -> List[FlagUsageProto]:
        interval_pb = TimestampProto()
        interval_pb.FromDatetime(datetime.utcnow())
        return [
            FlagUsageProto(
                name=name,
                interval=interval_pb,
                positive_count=0,
                negative_count=0,
            )
            for name in defaults
        ]
