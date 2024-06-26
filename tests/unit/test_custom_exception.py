from connexion.lifecycle import ConnexionResponse, ConnexionRequest
from unittest.mock import MagicMock, AsyncMock, patch

from asgimiddlewares.custom_exception import CustomExceptionMiddleware


@patch("asgimiddlewares.custom_exception.LOG")
def test_custom_exception_middleware(mock_log: MagicMock) -> None:
    request = ConnexionRequest({"type": "http"})
    exception = Exception("Test exception")
    mock_app = AsyncMock()

    middleware = CustomExceptionMiddleware(mock_app)

    response = middleware.common_error_handler(request, exception)

    assert isinstance(response, ConnexionResponse)
    assert response.status_code == 500
    assert mock_log.error.called
