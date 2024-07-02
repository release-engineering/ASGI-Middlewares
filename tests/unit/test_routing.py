from starlette.routing import Route, Mount
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


from asgimiddlewares import CustomRoutingMiddleware


@pytest.mark.parametrize(
    ["routes", "expected_order"],
    [
        pytest.param(
            [Route("/ping", lambda: "pong"), Route("/foo/{foo}", lambda foo: foo)],
            (1, 0),
        ),
        pytest.param(
            [
                Route("/foo", lambda: "foo"),
                Route("/foo/{bar}/{spam}", lambda bar, spam: (bar, spam)),
                Route("/foo/{bar}", lambda bar: bar),
            ],
            (2, 0, 1),
        ),
    ],
)
@patch("asgimiddlewares.routing.RoutingAPI")
def test_routing_middleware(
    mock_routing_api_constructor: MagicMock,
    routes: list[Route],
    expected_order: tuple[int],
):
    mock_app = AsyncMock()
    middleware = CustomRoutingMiddleware(mock_app)
    middleware.router = MagicMock()
    middleware.router.routes = [Mount("/v1", mock_app)]
    mock_api = mock_routing_api_constructor.return_value
    mock_api.router.routes = routes.copy()
    mock_api.base_path = "/v1"

    mock_specification = MagicMock()
    middleware.add_api(mock_specification, "/v1")

    mock_routing_api_constructor.assert_called_once_with(
        mock_specification, base_path="/v1", arguments=None, next_app=mock_app
    )

    # Check if routes are sorted  properly
    for route, index in zip(routes, expected_order):
        assert mock_api.router.routes[index] == route

    assert middleware.router.routes[0].app.default == mock_api.router

    middleware.router.mount.assert_called_once_with("/v1", app=mock_api.router)


@pytest.mark.asyncio
async def test_scope_change():
    middleware = CustomRoutingMiddleware(AsyncMock())
    mock_router = AsyncMock()
    middleware.router = mock_router
    scope = {"type": "http"}
    await middleware(scope, AsyncMock(), AsyncMock())
    assert scope["router"] == mock_router
