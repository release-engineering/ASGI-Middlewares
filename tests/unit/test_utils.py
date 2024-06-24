from unittest.mock import MagicMock

import pytest

from typing import Any

from opentelemetry.trace import INVALID_SPAN, Span

from asgimiddlewares.utils import replace_middleware, server_request_hook


@pytest.mark.parametrize(
    ["middleware_list", "original", "replacement", "expected"],
    [
        pytest.param(
            [1, 2, 3],
            2,
            4,
            [1, 4, 3],
            id="replace middle",
        )
    ],
)
def test_replace_middleware(
    middleware_list: list[Any], original: Any, replacement: Any, expected: Any
) -> None:
    """
    Find a specific class amongst a list of classes, and replace it.
    """
    replace_middleware(middleware_list, original, replacement)
    assert middleware_list == expected


def test_replace_middleware_exc() -> None:
    """
    Find a specific class amongst a list of classes, and replace it.
    """
    with pytest.raises(ValueError):
        replace_middleware([1, 2, 3], 5, 4)


@pytest.mark.parametrize(["span"], [(None,), (INVALID_SPAN,)])
def test_server_request_hook_with_no_span(span: Span) -> None:
    scope: dict[str, Any] = {"state": {}}
    server_request_hook(span, scope)
    assert "trace_id" not in scope["state"]


def test_server_request_hook() -> None:
    span = MagicMock()
    span.is_recording.return_value = True
    span.get_span_context.return_value.trace_id = 1234567890
    scope: dict[str, Any] = {"state": {}}
    server_request_hook(span, scope)
    assert scope["state"]["trace_id"] == "0x499602d2"
