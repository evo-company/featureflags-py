from featureflags_client.grpc.flags import Client
from featureflags_client.grpc.managers.dummy import DummyManager


def test():
    manager = DummyManager()

    class Defaults:
        FOO_FEATURE = False

    client = Client(Defaults, manager)

    with client.flags() as flags:
        assert flags.FOO_FEATURE is False
