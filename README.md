# Connexion-based ASGI Middleware Collection

This repository contains Connexion-based ASGI middleware collection for custom
logging, exception handling, tracing and observability as well as enhanced routing.

This project was developed in [Red Hat Inc.](https://www.redhat.com/en) as an effort
to add observability support for [Connexion 3](https://connexion.readthedocs.io/en/latest/).

## Quick Start

Simple usage example can be shown in the following snippet.

```python
from connexion import AsyncApp
from connexion.middleware import ConnexionMiddleware, MiddlewarePosition
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
# Security is normally right after routing, PathID needs to be after CustomRoutingMiddleware
your_app.add_middleware(PathIdMiddleware, position=MiddlewarePosition.BEFORE_SECURITY)

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


## Middlewares

This project intends to work with middlewares present in Connexion. The [default Connexion
stack](https://connexion.readthedocs.io/en/stable/middleware.html) looks like this:

- ServerErrorMiddleware
- ExceptionMiddleware
- SwaggerUIMiddleware
- RoutingMiddleware
- SecurityMiddleware
- RequestValidationMiddleware
- ResponseValidationMiddleware
- LifespanMiddleware
- ContextMiddleware

If you wish to use all middlewares contained in this repository, the recommended output
state will look like the following:

- ServerErrorMiddleware
- *OpenTelemetryMiddleware*
- **CustomHeaderMiddleware**
- **ExtendedLoggingMiddleware**
- **PrometheusMiddleware**
- **RequestTimeMiddleware**
- **CustomExceptionMiddleware**
- SwaggerUIMiddleware
- **CustomRoutingMiddleware**
- SecurityMiddleware
- RequestValidationMiddleware
- ResponseValidationMiddleware
- LifespanMiddleware
- **PathIdMiddleware**
- ContextMiddleware

### CustomExceptionMiddleware

This middleware adds a handler for internal server errors. It sends a log message of level
`error` and adds `trace_id` to the error details so customers are able to point maintainers
to an exact request.

**NOTE:** `trace_id` is taken from context variable which is filled in by `ExtendedLoggingMiddleware`.

**NOTE:** Make sure to allow the logger `asgimiddlewares` to log error messages if you want to utilize
this middleware.

#### Usage

This middleware is intended to replace Connexion's `ExceptionMiddleware` like so:

```python
middleware_stack = ConnexionMiddleware.default_middlewares
replace_middleware(middleware_stack, ExceptionMiddleware, CustomExceptionMiddleware)

your_app = AsyncApp("your_service", middlewares=middleware_stack)
```

### CustomHeaderMiddleware

This middleware adds additional fields to response headers. These fields are added:

- `trace_id` for observability
- `Content-Security-Policy` for XSS mitigation (disables all script sources as API is expected to return no scripts)

You can also disable the CSP header on some part of your API by specifying `csp_disable` argument.
This approach is good for using Swagger.

**NOTE:** `trace_id` requires 3rd party middleware, called 
[`OpenTelemetryMiddleware`](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/asgi/asgi.html#).

#### Usage

This middleware should also add headers before exceptions are handled so that
observability is possible even when errors occur.

The following snippet works if you use `CustomExceptionMiddleware` in your stack.

```python
your_app.add_middleware(
        CustomHeaderMiddleware,
        position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION,
        csp_disable=("/v1/ui", "/v2/ui", "/ui"),
    )
```

Otherwise use:

```python
your_app.add_middleware(
        CustomHeaderMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        csp_disable=("/v1/ui", "/v2/ui", "/ui"),
    )
```

### ExtendedLoggingMiddleware

This middleware allows you to extract more metadata from requests and responses and use
them in logging.

All output from this middleware is stored in [context variable](https://docs.python.org/3/library/contextvars.html)
`logging_ctx_var`.

For example you can define your own log formatter that uses this variable.

By default, this middleware adds all possible fields, which are:

- method
- path
- path_id (requires `PathIdMiddleware`)
- protocol
- query
- referer
- remote_address
- response_length
- status
- username (to be implemented)
- user_agent
- trace_id (requires `OpenTelemetryMiddleware`)
- True-Client-IP
- X-Akamai-RH-Edge-Id (specific for Red Hat use)
- X-Forwarded-For
- X-Forwarded-Proto
- X-Forwarded-Port
- X-Forwarded-Host

#### Usage

```python
connexion_app.add_middleware(
        ExtendedLoggingMiddleware,
        position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION,
        fields=("method", "path", "protocol", "response_length", ...)
    )
```

All the stored data can then be accessed by `logging_ctx_var.get()`. This variable is a dictionary
with keys being strings from the list above.

### PathIdMiddleware

This middleware adds variable `path_id` to scope, to be used by other middlewares 
(ExtendedLoggingMiddleware, PrometheusMiddleware). Path ID is argument-agnostic
endpoint path.

For example if we register endoint `/v1/foo/{bar}` and it receives a request (pointed
to `http://samplehost/v1/foo/spam`), scope gets another field, called `path_id` with
value `"/v1/foo/{bar}"`. Without this middleware, only field `path` with value `"/v1/foo/spam"`
would be present, which prevents effective log filtering.

If no match is found, this middleware fills the `path_id` as an empty stríng.

#### Usage

This middleware needs to be positioned after `CustomRoutingMiddleware`, but it does not need
to be immediately after it.

```python
your_app.add_middleware(PathIdMiddleware)
```

### PrometheusMiddleware

This middleware brings [Prometheus](https://prometheus.io/docs/prometheus/latest/getting_started/)
metrics support for observability of your application. It exposes the selected port
to export metrics about endpoint usage.

#### Usage

This middleware requires `PathIdMiddleware`.

To exclude paths from being tracked, pass them to the `excluded_paths` parameter.

```python
your_app.add_middleware(
    position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION,
    PrometheusMiddleware,
    service_name="cool_service",
    port=8000,
    excluded_paths=("", "/v1/ping", "/v1/ignore_me/{foo}"),
    )
```

### RequestTimeMiddleware

This middleware measures the time to process a request. Its output is present
in `request_time_ctx_vat` context variable and can be used for your needs.

For example you can define your own log formatter that uses this variable.

#### Usage

```python
your_app.add_middleware(
        RequestTimeMiddleware,
        position=CustomMiddlewarePosition.BEFORE_CUSTOM_EXCEPTION,
    )
```

### CustomRoutingMiddleware

This middleware is intended to replace Connexion's RoutingMiddleware. It solves
an [open issue in Connexion](https://github.com/spec-first/connexion/issues/1879)
and adds a router object to the scope to be used by `PathIdMiddleware`.

#### Usage

```python
replace_middleware(middleware_stack, functools.RoutingMiddleware, CustomRoutingMiddleware)
```

## Context variables

Some of the provided middlewares provide context variables to store the information
gathered for later use. The provided variables are:

- `logging_ctx_var: ContextVar[dict[str, typing.Any]]`, variable used for logging
  all selected fields from `ExtendedLoggingMiddleware`
- `request_time_ctx_var: ContextVar[float | None]`, variable used for keeping track
  of the request duration.

Recommended way of using the values of these variables is declaring your own log
formatter which uses these variables like so:

```python
class MyFormatter(logging.Formatter):
    def format(self, record):
        ...
        record["request_time"] = request_time_ctx_var.get()
        record["path_id"] = logging_ctx_var.get().get("path_id", "")
        ...
        return str(record)
```

For formatter reference, follow 
[this documentation](https://docs.python.org/3/library/logging.html#formatter-objects).
