from enum import Enum


class Endpoints(Enum):
    PRELOAD = "/flags/load"
    SYNC = "/flags/sync"
