from featureflags_client.grpc.client import FeatureFlagsClient
from featureflags_client.grpc.managers.dummy import DummyManager


def test():
    manager = DummyManager()

    class Defaults:
        FOO_FEATURE = False

    client = FeatureFlagsClient(Defaults, manager)

    with client.flags() as flags:
        assert flags.FOO_FEATURE is False
