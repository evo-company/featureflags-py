import logging

import config
import flags
from flask import Flask, g, request
from grpc import insecure_channel
from werkzeug.local import LocalProxy

from featureflags_client.grpc.client import FeatureFlagsClient
from featureflags_client.grpc.managers.sync import SyncManager

app = Flask(__name__)


def get_ff_client():
    ff_client = getattr(g, "_ff_client", None)
    if ff_client is None:
        channel = insecure_channel(f"{config.FF_HOST}:{config.FF_PORT}")
        manager = SyncManager(config.FF_PROJECT, [flags.REQUEST_QUERY], channel)
        ff_client = g._ff_client = FeatureFlagsClient(flags.Defaults, manager)
    return ff_client


def get_ff():
    if "_ff" not in g:
        g._ff_ctx = get_ff_client().flags(
            {
                flags.REQUEST_QUERY.name: request.query_string,
            }
        )
        g._ff = g._ff_ctx.__enter__()
    return g._ff


@app.teardown_request
def teardown_request(exception=None):
    if "_ff" in g:
        g._ff_ctx.__exit__(None, None, None)
        del g._ff_ctx
        del g._ff


ff = LocalProxy(get_ff)


@app.route("/")
def index():
    if ff.TEST:
        return "TEST: True"
    else:
        return "TEST: False"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("featureflags").setLevel(logging.DEBUG)

    app.run(port=5000)
