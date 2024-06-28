""" Middleware for handling extended logging """

from typing import Dict, List, Tuple, Iterable

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send, Message

from .utils import logging_ctx_var


_FIELD_MAPPING = {
    "method": lambda scope, headers: scope.get("method"),
    "path": lambda scope, headers: scope.get("path"),
    "path_id": lambda scope, headers: None,  # handled in response
    "protocol": lambda scope, headers: f"{scope.get('type')}"
    f"/{scope.get('http_version')}",
    "query": lambda scope, headers: scope.get("query_string", b"").decode("utf-8"),
    "referer": lambda scope, headers: headers.get("referer"),
    "remote_address": lambda scope, headers: scope.get("client", ("-", "-"))[0],
    "response_length": lambda scope, headers: None,  # handled in response
    "status": lambda scope, headers: None,  # handled in response
    "username": lambda scope, headers: "-",  # TODO
    "user_agent": lambda scope, headers: headers.get("user-agent"),
    "trace_id": lambda scope, headers: scope["state"].get("trace_id", "-"),
    "True-Client-IP": lambda scope, headers: headers.get("true-client-ip"),
    "X-Akamai-RH-Edge-Id": lambda scope, headers: headers.get("x-rh-edge-request-id"),
    "X-Forwarded-For": lambda scope, headers: headers.get("x-forwarded-for"),
    "X-Forwarded-Proto": lambda scope, headers: headers.get("x-forwarded-proto"),
    "X-Forwarded-Port": lambda scope, headers: headers.get("x-forwarded-port"),
    "X-Forwarded-Host": lambda scope, headers: headers.get("x-forwarded-host"),
}
POSSIBLE_FIELDS = list(_FIELD_MAPPING.keys())


DEFAULT_SETTINGS = tuple(POSSIBLE_FIELDS)


def parse_headers(headers: List[Tuple[bytes, bytes]]) -> Dict[str, str]:
    """
    Parse scope headers into a dictionary

    Args:
        headers (List[bytes, bytes]]): List of headers

    Returns:
        Dict[str, str]: Dictionary of headers
    """
    return {pair[0].decode("utf-8"): pair[1].decode("utf-8") for pair in headers}


class ExtendedLoggingMiddleware:  # pylint: disable=too-few-public-methods
    """
    Custom middleware to make selected request related
    variables available outside of the request loop.
    """

    def __init__(self, app: ASGIApp, fields: Iterable[str] = DEFAULT_SETTINGS) -> None:
        """
        To override default fields, use functools.partial() with the required
        keyword argument.

        :param app: ASGI application or next middleware.
                    Is called in the middleware stack.
        :param fields: Fields to be included in the logging.
                       See POSSIBLE_FIELDS for possible fields.
        """
        for field in fields:
            if field not in _FIELD_MAPPING:
                raise ValueError(f"Unknown field to log: '{field}'!")
        self.app = app
        self.fields = fields

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_headers = parse_headers(scope.get("headers", []))

        # base uvicorn.access log structure
        # values from scope, send.message or headers
        data = {key: _FIELD_MAPPING[key](scope, scope_headers) for key in self.fields}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Fill in fields that require to be filled
                # after the request is processed
                if "status" in data:
                    data["status"] = message["status"]
                if "path_id" in data:
                    data["path_id"] = scope.get("state", {}).get("path_id")
                headers = Headers(scope=message)
                if "response_length" in data:
                    data["response_length"] = int(headers.get("content-length", 0))

            await send(message)

        logging_ctx_var.set(data)

        await self.app(scope, receive, send_wrapper)
