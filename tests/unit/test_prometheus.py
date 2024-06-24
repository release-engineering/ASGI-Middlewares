from typing import Iterable, Dict, Any, Optional
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from asgimiddlewares.prometheus import (
    _setup_prometheus,
    PrometheusMiddleware,
)


@patch("asgimiddlewares.prometheus.start_http_server")
@patch("asgimiddlewares.prometheus.multiprocess.MultiProcessCollector")
@patch("asgimiddlewares.prometheus.CollectorRegistry")
@pytest.mark.parametrize(["port"], [(1,), ("1",)])
def test_setup_prometheus(
    mock_registry: MagicMock,
    mock_multiprocess_collector: MagicMock,
    mock_start_server: MagicMock,
    port: Any,
):
    _setup_prometheus(port)
    mock_start_server.assert_called_once_with(port)
    mock_registry.assert_called_once()
    mock_multiprocess_collector.assert_called_once_with(mock_registry())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["excluded_paths", "scope", "endpoint_for_metrics"],
    [
        (
            ["/v1/ping"],
            {"path": "/v1/sample", "method": "GET", "state": {"path_id": "/v1/sample"}},
            "/v1/sample",
        ),
        (["/v1/ping"], {"path": "/v1/ping", "method": "GET", "path_params": {}}, None),
        (
            [],
            {
                "path": "/v1/sample/id/123",
                "method": "GET",
                "state": {"path_id": "/v1/sample/id/<identifier>"},
            },
            "/v1/sample/id/<identifier>",
        ),
        (
            [],
            {
                "path": "/v1/sample/id/123/other/456",
                "method": "GET",
                "state": {"path_id": "/v1/sample/id/<identifierA>/other/<identifierB>"},
            },
            "/v1/sample/id/<identifierA>/other/<identifierB>",
        ),
    ],
)
@patch(
    "asgimiddlewares.prometheus.time.perf_counter",
    MagicMock(return_value=0),
)
@patch("asgimiddlewares.prometheus.Counter")
@patch("asgimiddlewares.prometheus.Histogram")
@patch("asgimiddlewares.prometheus.disable_created_metrics")
@patch("asgimiddlewares.prometheus.prometheus_client.REGISTRY.unregister")
@patch("asgimiddlewares.prometheus._setup_prometheus")
async def test_prometheus_middleware(
    mock_setup_prometheus: MagicMock,
    mock_unregister: MagicMock,
    mock_disable_create: MagicMock,
    mock_histogram_constructor: MagicMock,
    mock_counter_constructor: MagicMock,
    excluded_paths: Iterable[str],
    scope: Dict[str, Any],
    endpoint_for_metrics: Optional[str],
) -> None:
    # ASGI app is a callable
    mock_app = AsyncMock()

    # This step would normally be done inside Connexion
    middleware = PrometheusMiddleware(
        mock_app, service_name="foo", port=5002, excluded_paths=excluded_paths
    )
    middleware.hostname = "Marvin"
    mock_setup_prometheus.assert_called_once_with(5002)
    mock_counter_constructor.assert_called_once()
    mock_histogram_constructor.assert_called_once()
    # The middleware uses a set, duplicates will be deleted
    for excluded_path in excluded_paths:
        assert excluded_path in middleware.excluded_paths
    # Check for function called in the constructor to reduce metrics
    mock_disable_create.assert_called_once()
    mock_unregister.assert_called()

    # Call the middleware, simulates Connexion's stack.
    # This is called when a request is made.
    await middleware(scope, AsyncMock(), AsyncMock())

    mock_app.assert_called_once()
    # This is a simple hack to call the "send" function
    # which would otherwise be called in the middleware stack.
    _, __, send = mock_app.call_args.args
    await send({"type": "http.response.start", "status": 200})

    if endpoint_for_metrics is not None:
        method = scope["method"]
        # Check if correct labels were applied
        middleware.counter.labels.assert_called_once_with("Marvin", "200", method)
        middleware.histogram.labels.assert_called_once_with(
            "Marvin", "200", method, endpoint_for_metrics
        )

        # Check if correct call was made on the labels
        middleware.counter.labels.return_value.inc.assert_called_once_with(1)
        middleware.histogram.labels.return_value.observe.assert_called_once_with(0)
    else:
        # Nothing was incremented if the endpoint is supposed to be ignored
        middleware.counter.labels.assert_not_called()
        middleware.histogram.labels.assert_not_called()

        middleware.counter.labels.return_value.inc.assert_not_called()
        middleware.histogram.labels.return_value.observe.assert_not_called()
