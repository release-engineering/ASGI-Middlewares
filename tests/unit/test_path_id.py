import pytest

from unittest.mock import AsyncMock, MagicMock

from starlette.routing import Route, Mount, WebSocket, Router

from asgimiddlewares import PathIdMiddleware


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["path", "expected"],
    [
        ("/v1/ping", "/v1/ping"),
        ("/v1/foo/bar", "/v1/foo/{foo}"),
        ("/v2/ping", "/v2/ping"),
        ("/v1/ui/", ""),
    ],
)
async def test_path_id_middleware(path: str, expected: str):
    middleware = PathIdMiddleware(AsyncMock())

    mock_router = AsyncMock()

    mock_socket = WebSocket({"type": "websocket"}, MagicMock(), MagicMock())

    mock_mount0 = Mount("/v0", MagicMock())
    mock_mount1 = Mount("/v1", MagicMock(spec=Router))
    mock_mount2 = Mount("/v2", MagicMock(spec=Router))
    mock_router.routes = [mock_socket, mock_mount0, mock_mount1, mock_mount2]
    route1 = Route("/ping", lambda: "pong")
    route2 = Route("/foo/{foo}", lambda foo: f"bar: {foo}")

    mock_mount1.app.routes = [route1, route2]
    mock_mount2.app.routes = [mock_socket, route1]

    mock_scope = {
        "router": mock_router,
        "path": path,
        "type": "http",
        "state": {},
        "method": "GET",
    }
    await middleware(mock_scope, AsyncMock(), AsyncMock())
    assert mock_scope["state"]["path_id"] == expected


@pytest.mark.asyncio
async def test_middleware_exception():
    mock_scope = {
        "path": "/path",
        "type": "http",
        "state": {},
        "method": "GET",
    }
    middleware = PathIdMiddleware(AsyncMock())
    with pytest.raises(KeyError):
        await middleware(mock_scope, AsyncMock(), AsyncMock())
