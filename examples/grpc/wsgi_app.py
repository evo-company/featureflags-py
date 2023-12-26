import logging

import config
import flags
from grpc import insecure_channel

from featureflags_client.grpc.client import FeatureFlagsClient
from featureflags_client.grpc.managers.sync import SyncManager


def make_app():
    channel = insecure_channel(f"{config.FF_HOST}:{config.FF_PORT}")
    manager = SyncManager(config.FF_PROJECT, [flags.REQUEST_QUERY], channel)
    client = FeatureFlagsClient(flags.Defaults, manager)

    def application(environ, start_response):
        ctx = {flags.REQUEST_QUERY.name: environ["QUERY_STRING"]}
        with client.flags(ctx) as ff:
            content = b"TEST: True" if ff.TEST else b"TEST: False"

        start_response("200 OK", [("Content-Length", str(len(content)))])
        return [content]

    return application


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("featureflags").setLevel(logging.DEBUG)

    from wsgiref.simple_server import make_server

    with make_server("", 5000, make_app()) as server:
        server.serve_forever()
