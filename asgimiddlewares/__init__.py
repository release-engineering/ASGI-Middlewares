"""Connexion-based ASGI middleware collection with utilities."""

import enum

from asgimiddlewares.custom_exception import CustomExceptionMiddleware
from asgimiddlewares.custom_header import CustomHeaderMiddleware
from asgimiddlewares.extended_logging import ExtendedLoggingMiddleware
from asgimiddlewares.path_id import PathIdMiddleware
from asgimiddlewares.prometheus import PrometheusMiddleware
from asgimiddlewares.request_time import RequestTimeMiddleware
from asgimiddlewares.routing import CustomRoutingMiddleware
from asgimiddlewares.utils import (
    replace_middleware,
    server_request_hook,
    request_time_ctx_var,
    logging_ctx_var,
)

__all__ = [
    "CustomExceptionMiddleware",
    "CustomHeaderMiddleware",
    "ExtendedLoggingMiddleware",
    "PathIdMiddleware",
    "PrometheusMiddleware",
    "RequestTimeMiddleware",
    "CustomRoutingMiddleware",
    "replace_middleware",
    "server_request_hook",
    "CustomMiddlewarePosition",
    "request_time_ctx_var",
    "logging_ctx_var",
]


class CustomMiddlewarePosition(enum.Enum):
    """
    Custom enum for positioning middlewares. Imitates Connexion's MiddlewarePosition.

    Replace BEFORE_EXCEPTION
    """

    BEFORE_CUSTOM_EXCEPTION = CustomExceptionMiddleware
    BEFORE_ROUTING = CustomRoutingMiddleware
