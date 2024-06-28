""" Custom middleware to handle exception with extra logging """

import logging


from connexion.exceptions import InternalServerError
from connexion.lifecycle import ConnexionResponse
from connexion.middleware.exceptions import ExceptionMiddleware

from starlette.requests import Request

from .utils import logging_ctx_var

LOG = logging.getLogger(__name__)


class CustomExceptionMiddleware(
    ExceptionMiddleware  # type: ignore
):  # pylint: disable=too-few-public-methods
    """Custom Exception Middleware to handle unhandled exceptions"""

    @staticmethod
    def common_error_handler(_request: Request, exc: Exception) -> ConnexionResponse:
        """Default handler for any unhandled Exception"""
        LOG.error(
            {
                "message": "Unhandled exception occurred",
                "unhandled_exception": True,
            },
            exc_info=exc,
        )
        # this is needed as the unhandled exception are not
        # caught by the error handlers
        internal_server_error = InternalServerError()
        internal_server_error.ext = {"trace_id": logging_ctx_var.get().get("trace_id")}

        return internal_server_error.to_problem()
