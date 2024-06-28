# ASGI Middleware Collection

This repository contains Connexion-based ASGI middleware collection for custom
logging, exception handling, tracing and observability as well as enhanced routing.

## Quick Start

Simple usage example can be shown in the following snippet.

```python
from connexion import AsyncApp
from connexion.middleware import ConnexionMiddleware
from connexion.middleware.exceptions import ExceptionMiddleware
from connexion.middleware.routing import RoutingMiddleware
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from asgimiddlewares import *

middleware_stack = ConnexionMiddleware.default_middlewares
replace_middleware(middleware_stack, ExceptionMiddleware, CustomExceptionMiddleware)
replace_middleware(middleware_stack, RoutingMiddleware, CustomRoutingMiddleware)

provider = TracerProvider(resource=Resource.create())


your_app = AsyncApp("your_service", middlewares=middleware_stack)
your_app.add_middleware(
    OpenTelemetryMiddleware,
    tracer_provider=provider,
    server_request_hook=server_request_hook,
    position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION,
)
your_app.add_middleware(
    CustomHeaderMiddleware, position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION
)
your_app.add_middleware(PathIdMiddleware)

your_app.add_api(
    {
        "info": {"title": "sample", "version": "1"},
        "openapi": "3.0.0",
        "paths": {
            "/ping": {
                "get": {
                    "operationId": "ping.ping",  # File ping.py contains function ping that returns sample string
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
)

your_app.run()
```

As written in the snippet, you also need a file `ping.py` containing the endpoint logic like so:

```python
def ping():
    return "pong"
```

Now you can test your sample application by running:

```shell
curl -v http://localhost:8000/ping
```

You will see that additional headers are added to the response message.

## Usage

If you wish to override any Middleware default settings, use `functools.partial` like so:

```python
from connexion import AsyncApp
import functools
from asgimiddlewares import ExtendedLoggingMiddleware, CustomMiddlewarePosition

your_app = AsyncApp("sample")

custom_middleware = functools.partial(
    ExtendedLoggingMiddleware, fields=("method", "path_id")
)
your_app.add_middleware(
    custom_middleware, 
    position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION
)
```

## Middleware positions

Each middleware is required to have a fixed position in the middleware stack.

Custom Logging, Custom Header, Prometheus and Request Time need to be located
before the Exception Middleware to be able to log errors.

Path ID needs to be positioned after routing middleware, position before
Connexion's Context middleware (default middleware position) also works.

Custom Routing and Custom Exception need to substitute Connexion's original
middlewares. For this purpose, function `replace_middleware` can be used.

To position your middlewares accordingly, use `CustomMiddlewarePosition` enum.

## Context variables

Some of the provided middlewares provide context variables to store the information
gathered for later use. The provided variables are:

- `logging_ctx_var: ContextVar[dict[str, typing.Any]]`, variable used for logging
  all selected fields from `ExtendedLoggingMiddleware`
- `request_time_ctx_var: ContextVar[float | None]`, variable used for keeping track
  of the request duration.
