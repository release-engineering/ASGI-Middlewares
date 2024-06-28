import pytest

from typing import Any, Dict
from unittest.mock import MagicMock, AsyncMock, patch

from asgimiddlewares.utils import logging_ctx_var
from asgimiddlewares.extended_logging import (
    parse_headers,
    ExtendedLoggingMiddleware,
)


def test_parse_headers_empty() -> None:
    headers = []
    result = parse_headers(headers)
    assert result == {}


def test_parse_headers_multiple_headers() -> None:
    headers = [
        (b"Content-Type", b"application/json"),
        (b"Authorization", b"Bearer token"),
        (b"X-Request-ID", b"1234567890"),
    ]
    result = parse_headers(headers)
    assert result == {
        "Content-Type": "application/json",
        "Authorization": "Bearer token",
        "X-Request-ID": "1234567890",
    }


@pytest.mark.parametrize(
    ("scope", "message"),
    [
        pytest.param(
            {
                "method": "GET",
                "path": "/v1/path/a/to/b/somewhere/c",
                "path_params": {"a": "a", "b": "b", "c": "c"},
                "type": "http",
                "http_version": "1.1",
                "query_string": b"test",
                "state": {
                    "trace_id": "0x5d66f33f56b69ead5d79f7a928fde097",
                    "path_id": "/v1/path/<a>/to/<b>/somewhere/<c>",
                },
                "client": ("a.b.c.d", 12345),
                "headers": [
                    (b"referer", b"john_doe"),
                    (b"user-agent", b"curl/7.76.1"),
                    (b"true-client-ip", b"a.b.c.d"),
                    (b"x-rh-edge-request-id", b"id"),
                    (b"x-forwarded-for", b"for"),
                    (b"x-forwarded-proto", b"proto"),
                    (b"x-forwarded-port", b"port"),
                    (b"x-forwarded-host", b"host"),
                ],
            },
            {"type": "http.response.start", "status": 200},
        )
    ],
)
@pytest.mark.parametrize(
    ("headers", "expected", "tracked_fields"),
    [
        pytest.param(
            {"content-length": b"123"},
            {
                "method": "GET",
                "path": "/v1/path/a/to/b/somewhere/c",
                "path_id": "/v1/path/<a>/to/<b>/somewhere/<c>",
                "protocol": "http/1.1",
                "query": "test",
                "referer": "john_doe",
                "remote_address": "a.b.c.d",
                "response_length": 123,
                "status": 200,
                "username": "-",
                "user_agent": "curl/7.76.1",
                "trace_id": "0x5d66f33f56b69ead5d79f7a928fde097",
                "True-Client-IP": "a.b.c.d",
                "X-Akamai-RH-Edge-Id": "id",
                "X-Forwarded-For": "for",
                "X-Forwarded-Proto": "proto",
                "X-Forwarded-Port": "port",
                "X-Forwarded-Host": "host",
            },
            None,
            id="content-length present",
        ),
        pytest.param(
            {},
            {
                "method": "GET",
                "path": "/v1/path/a/to/b/somewhere/c",
                "path_id": "/v1/path/<a>/to/<b>/somewhere/<c>",
                "protocol": "http/1.1",
                "query": "test",
                "referer": "john_doe",
                "remote_address": "a.b.c.d",
                "response_length": 0,
                "status": 200,
                "username": "-",
                "user_agent": "curl/7.76.1",
                "trace_id": "0x5d66f33f56b69ead5d79f7a928fde097",
                "True-Client-IP": "a.b.c.d",
                "X-Akamai-RH-Edge-Id": "id",
                "X-Forwarded-For": "for",
                "X-Forwarded-Proto": "proto",
                "X-Forwarded-Port": "port",
                "X-Forwarded-Host": "host",
            },
            None,
            id="content-length missing",
        ),
        pytest.param(
            {},
            {
                "path": "/v1/path/a/to/b/somewhere/c",
                "path_id": "/v1/path/<a>/to/<b>/somewhere/<c>",
                "query": "test",
            },
            ["path", "path_id", "query"],
        ),
    ],
)
@patch("asgimiddlewares.extended_logging.Headers")
@pytest.mark.asyncio
async def test_extended_logging_middleware(
    mock_headers: MagicMock,
    scope: Dict[str, Any],
    message: Dict[str, Any],
    expected: Dict[str, Any],
    tracked_fields: list[str],
    headers: Dict[str, Any],
) -> None:
    mock_app = AsyncMock()
    mock_headers.return_value = headers
    if tracked_fields is not None:
        middleware = ExtendedLoggingMiddleware(mock_app, tracked_fields)
    else:
        middleware = ExtendedLoggingMiddleware(mock_app)

    await middleware(scope, AsyncMock(), AsyncMock())

    mock_app.assert_called_once()

    _, __, send = mock_app.call_args.args
    await send(message)

    assert logging_ctx_var.get() == expected


def test_extended_logging_middleware_invalid_field():
    with pytest.raises(ValueError, match="Unknown field to log: 'foo'!"):
        ExtendedLoggingMiddleware(MagicMock(), ("foo", "boar"))
