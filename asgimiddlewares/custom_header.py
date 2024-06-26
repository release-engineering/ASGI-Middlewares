""" Middleware for working with response headers """

from typing import Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send, Message


class CustomHeaderMiddleware:  # pylint: disable=too-few-public-methods
    """
    Custom ASGI Header Middleware

    Extends header with trace_id and CSP
    """

    def __init__(
        self, app: ASGIApp, csp_disable: Iterable[str] = ("/ui", "/v1/ui")
    ) -> None:
        """
        To override default base_paths, use functools.partial() with the required
        kwargs.

        :param Iterable[str] csp_disable: Specify all paths that should not receive the
        CSP header. ALL paths that START with any of the strings from this iterable are
        disabled. That means string '/v1/ui' disables also path '/v1/ui/#'.
        """
        self.app = app
        self.csp_disable = set(csp_disable)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_with_extra_headers(message: Message) -> None:
            if message.get("type") == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("trace_id", scope["state"].get("trace_id", "-"))

                path = scope.get("path", "")
                # handle CSP
                if all(not path.startswith(disable) for disable in self.csp_disable):
                    headers.append(
                        "Content-Security-Policy",
                        "default-src 'none'; frame-ancestors 'none'",
                    )

            await send(message)

        await self.app(scope, receive, send_with_extra_headers)
