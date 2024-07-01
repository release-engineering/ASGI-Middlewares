import pytest

from unittest.mock import AsyncMock
from typing import Any

from asgimiddlewares import PathIdMiddleware


@pytest.mark.parametrize(
    ["scope", "result"],
    [
        pytest.param({"state": {}}, ""),
        pytest.param({"state": {}, "path": "v1/ping"}, "v1/ping"),
        pytest.param(
            {
                "state": {},
                "path": "v1/foo/aaa/bar/bbb",
                "path_params": {"paramA": "aaa", "paramB": "bbb"},
            },
            "v1/foo/<paramA>/bar/<paramB>",
        ),
        pytest.param(
            {
                "state": {},
                "path": "/v1/foo/foo_id/bar/bar_id",
                "path_params": {"foo": "foo_id", "bar": "bar_id"},
            },
            "/v1/foo/<foo>/bar/<bar>",
        ),
        pytest.param(
            {
                "state": {},
                "path": "/v1/foo/1/bar/1",
                "path_params": {"foo": "1", "bar": "1"},
            },
            "/v1/foo/<foo>/bar/<bar>",
        ),
        pytest.param(
            {
                "state": {},
                "path": "/v1/foo/1/bar/1",
                "path_params": {"foo": 1, "bar": "1"},
            },
            "/v1/foo/<foo>/bar/<bar>",
        ),
        pytest.param(
            {
                "state": {},
                "path": "/v1/foo/foo/bar/bar",
                "path_params": {"foo": "foo", "bar": "bar"},
            },
            "/v1/foo/<foo>/bar/<bar>",
        ),
        pytest.param(
            {
                "state": {},
                "path": "/v1/foo/foo/bar/foo",
                "path_params": {"foo": "foo", "bar": "foo"},
            },
            "/v1/foo/<foo>/bar/<bar>",
        ),
    ],
)
@pytest.mark.asyncio
async def test_path_id_middleware(scope: dict[str, Any], result: str) -> None:
    mock_app = AsyncMock()
    middleware = PathIdMiddleware(mock_app)
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    await middleware(scope, mock_receive, mock_send)

    assert scope.get("state", {}).get("path_id") == result
