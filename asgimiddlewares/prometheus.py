"""Custom Prometheus middleware designed specifically for
Connexion AsyncApp. It has to be added BEFORE EXCEPTION,
which is by the end of the Middleware stack.

It requires the environment variable PROMETHEUS_MULTIPROC_DIR."""

import os
import time
from typing import Iterable, Any

import prometheus_client

from prometheus_client import (
    Counter,
    Histogram,
    disable_created_metrics,
    PROCESS_COLLECTOR,
    PLATFORM_COLLECTOR,
    GC_COLLECTOR,
    CollectorRegistry,
    multiprocess,
    start_http_server,
)
from starlette.types import ASGIApp, Scope, Receive, Send


def _setup_prometheus(port: int) -> None:
    """Starts an HTTP prometheus multiprocessing server at the specified port."""
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    start_http_server(port)


__all__ = ["PrometheusMiddleware"]


# pylint: disable=too-few-public-methods
class PrometheusMiddleware:
    """Connexion Middleware class for Prometheus metrics exposure."""

    def __init__(
        self,
        app: ASGIApp,
        service_name: str = "",
        port: int = 5001,
        excluded_paths: Iterable[str] = ("",),
    ):
        """
        This constructor is intended to be called inside a Connexion
        middleware stack and not by the user. To add it to the stack,
        use app.add_middleware(PrometheusMiddleware). If you wish to
        specify non_default arguments, use functools.partial() to pass
        them as kwargs.

        :param ASGIApp app: ASGI app or a middleware layer.
        :param str service_name: Name of the service to appear in Prometheus metrics,
        defaults to empty string.
        :param int port: Port to expose the metrics, defaults to 5001.
        :param Iterable[str] excluded_paths: Endpoints to exclude from metrics.
        If you wish to exclude an endpoint containing a variable,
        enclose all variables in {curly braces} like so:
        `excluded_paths=("/v1/sample/id/{identifier}",)`
        """
        _setup_prometheus(port)
        if service_name:
            service_name = f"{service_name}_"
        self.counter = Counter(
            f"{service_name}http_request_total",
            "Accesses of HTTP endpoints",
            labelnames=("hostname", "status", "method"),
        )
        self.histogram = Histogram(
            f"{service_name}http_request_duration_seconds",
            "HTTP request duration in seconds",
            labelnames=("hostname", "status", "method", "url_rule"),
        )
        self.hostname = os.environ.get("HOSTNAME", "localhost")

        self.app: ASGIApp = app
        # Disable measuring the UNIX time when a metric was created
        disable_created_metrics()
        # Disable metrics related to the host
        for collector in (PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR):
            prometheus_client.REGISTRY.unregister(collector)
        self.excluded_paths = set(excluded_paths)

    async def _timed_call(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Wrap the request execution to measure the time of execution.
        :param Scope scope: Mapping passed along with the ASGI request.
        :param Receive receive: Callable object for request manipulation.
        :param Send send: Callable object for response manipulation.
        :return: None
        """
        method = scope["method"]
        time_ref = time.perf_counter()

        async def wrapped_send(response: Any) -> None:
            """
            Wrapped send function to measure the metrics.
            :param response: Mapping representing an HTTP response.
            :return: Calls an ASGI `send` function and returns its value.
            """
            # Measure time upon receiving the response head
            if response["type"] == "http.response.start":
                status_code = str(response["status"])
                # get path_id prepared by the PathIdMiddleware
                path_id = scope.get("state", {}).get("path_id")
                self.histogram.labels(
                    self.hostname, status_code, method, path_id
                ).observe(time.perf_counter() - time_ref)
                self.counter.labels(self.hostname, status_code, method).inc(1)
            await send(response)

        await self.app(scope, receive, wrapped_send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Use the middleware. Called inside the connexion middleware stack.
        :param Scope scope: Mapping passed along with the ASGI request.
        :param Receive receive: Callable object for request manipulation.
        :param Send send: Callable object for response manipulation.
        """
        if "path" in scope:
            if scope["path"] not in self.excluded_paths:
                await self._timed_call(scope, receive, send)
                return
        await self.app(scope, receive, send)
