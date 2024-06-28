"""Utilities for middleware placement and context handling."""

from typing import Any, Optional
from contextvars import ContextVar

from opentelemetry.trace import Span, INVALID_SPAN
from starlette.types import Scope

logging_ctx_var: ContextVar[dict[str, Any]] = ContextVar("extended_logs", default={})

request_time_ctx_var: ContextVar[Optional[float]] = ContextVar(
    "request_time", default=None
)


def replace_middleware(
    middleware_list: list[Any], original: Any, replacement: Any
) -> None:
    """
    Find a specific class amongst a list of classes, and replace it.
    """
    for i, middleware in enumerate(middleware_list):
        if middleware == original:
            middleware_list.pop(i)
            middleware_list.insert(i, replacement)
            return
    raise ValueError(f"Middleware {original} not found in the list of middlewares")


def server_request_hook(span: Span, scope: Scope) -> None:
    """Request hook to store trace_id to the scope"""
    # We need to check even unrecorded spans.
    # Unrecorded spans can be set by traceparent header
    # with unsampled flag, see https://www.w3.org/TR/trace-context/#traceparent-header
    # but trace_id is also used for debugging purposes
    if span and span != INVALID_SPAN:
        trace_id = None
        span_context = span.get_span_context()
        if span_context.trace_id != 0:
            # trace_id 0 means invalid span
            trace_id = str(hex(span_context.trace_id))
        scope["state"]["trace_id"] = trace_id
