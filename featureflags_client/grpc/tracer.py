from collections import OrderedDict
from datetime import datetime


class Tracer:
    """
    Accumulates request/flag/values
    """

    def __init__(self) -> None:
        self.values: OrderedDict[str, int] = OrderedDict()
        self.interval = datetime.utcnow().replace(second=0, microsecond=0)

    def inc(self, name: str, value: int) -> None:
        self.values[name] = value
