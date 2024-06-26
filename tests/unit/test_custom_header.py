import pytest

from unittest.mock import AsyncMock

from asgimiddlewares import CustomHeaderMiddleware


@pytest.mark.asyncio
async def test_custom_header_middleware_with_csp() -> None:
    mock_app = AsyncMock()
    middleware = CustomHeaderMiddleware(mock_app)
    scope = {"type": "http", "path": "/some-path", "state": {"trace_id": "123456"}}
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    await middleware(scope, mock_receive, mock_send)

    _, __, send_with_extra_headers_call = mock_app.call_args.args
    assert send_with_extra_headers_call is not None

    await send_with_extra_headers_call(
        {"type": "http.response.start", "status": 200, "headers": []}
    )

    mock_send.assert_awaited_once_with(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"trace_id", b"123456"),
                (
                    b"content-security-policy",
                    b"default-src 'none'; frame-ancestors 'none'",
                ),
            ],
        }
    )


@pytest.mark.parametrize(
    "request_path",
    [
        "/ui",
        "/v1/ui/#/Certification projects/graphql.cert_projects.replace_certification_project",
    ],
)
@pytest.mark.asyncio
async def test_custom_header_middleware_without_csp(request_path: str) -> None:
    mock_app = AsyncMock()
    middleware = CustomHeaderMiddleware(mock_app)
    scope = {"type": "http", "path": request_path, "state": {"trace_id": "123456"}}
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    await middleware(scope, mock_receive, mock_send)

    _, __, send_with_extra_headers_call = mock_app.call_args.args
    assert send_with_extra_headers_call is not None

    await send_with_extra_headers_call(
        {"type": "http.response.start", "status": 200, "headers": []}
    )
    mock_send.assert_awaited_once_with(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"trace_id", b"123456"),
            ],
        }
    )


@pytest.mark.asyncio
async def test_custom_header_middleware_websocket() -> None:
    mock_app = AsyncMock()
    middleware = CustomHeaderMiddleware(mock_app)
    scope = {"type": "websocket", "path": "/some-path", "state": {"trace_id": "123456"}}

    await middleware(scope, AsyncMock(), AsyncMock())
    mock_app.assert_called_once()
