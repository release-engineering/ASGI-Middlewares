import pytest

from unittest.mock import AsyncMock

from asgimiddlewares.utils import request_time_ctx_var
from asgimiddlewares import RequestTimeMiddleware


@pytest.mark.asyncio
async def test_request_time_middleware() -> None:
    mock_app = AsyncMock()
    middleware = RequestTimeMiddleware(mock_app)

    await middleware({}, AsyncMock(), AsyncMock())

    mock_app.assert_called_once()

    _, __, send = mock_app.call_args.args
    await send({"type": "http.response.start", "status": 200})

    assert request_time_ctx_var.get() is not None
    assert isinstance(request_time_ctx_var.get(), float)
