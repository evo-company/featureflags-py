import logging

import config
import flags
from aiohttp import web

from featureflags_client.http.client import FeatureFlagsClient
from featureflags_client.http.managers.httpx import HttpxManager

log = logging.getLogger(__name__)


async def on_start(app):
    app["ff_manager"] = HttpxManager(
        url=config.FF_URL,
        project=config.FF_PROJECT,
        variables=[flags.REQUEST_QUERY],
        defaults=flags.Defaults,
        request_timeout=5,
        refresh_interval=10,
    )
    app["ff_client"] = FeatureFlagsClient(app["ff_manager"])

    try:
        await app["ff_client"].preload_async()
    except Exception:
        log.exception(
            "Unable to preload feature flags, application will "
            "start working with defaults and retry later"
        )

    # Async managers need to `start` and `wait_closed` to be able to
    # run flags update loop
    app["ff_manager"].start()


async def on_stop(app):
    await app["ff_manager"].wait_closed()


@web.middleware
async def middleware(request, handler):
    ctx = {flags.REQUEST_QUERY.name: request.query_string}
    with request.app["ff_client"].flags(ctx) as ff:
        request["ff"] = ff
        return await handler(request)


async def index(request):
    if request["ff"].TEST:
        return web.Response(text="TEST: True")
    else:
        return web.Response(text="TEST: False")


def create_app():
    app = web.Application(middlewares=[middleware])

    app.router.add_get("/", index)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_stop)

    app["config"] = config

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("featureflags").setLevel(logging.DEBUG)

    web.run_app(create_app(), port=5000)
