import pytest

from featureflags_client.grpc.conditions import load_flags
from featureflags_client.grpc.flags import AbstractManager


class SimpleManager(AbstractManager):
    def __init__(self):
        self.checks = {}

    def preload(self, timeout=None, defaults=None) -> None:
        pass

    def load(self, result):
        self.checks = load_flags(result)

    def get(self, name):
        return self.checks.get(name)

    def add_trace(self, tracer):
        pass


@pytest.fixture()
def simple_manager():
    return SimpleManager()
