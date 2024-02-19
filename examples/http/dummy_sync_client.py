import logging

import config
import flags
from flask import Flask, g, request
from werkzeug.local import LocalProxy

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.dummy import DummyManager

app = Flask(__name__)


def get_ff_client():
    ff_client = getattr(g, "_ff_client", None)
    if ff_client is None:
        # Dummy manager just uses Defaults values for flags, mainly for tests.
        manager = DummyManager(
            url=config.FF_URL,
            project=config.FF_PROJECT,
            variables=[flags.REQUEST_QUERY],
            defaults=flags.Defaults,
            request_timeout=5,
            refresh_interval=10,
        )
        ff_client = g._ff_client = FeatureFlagsClient(manager)
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
