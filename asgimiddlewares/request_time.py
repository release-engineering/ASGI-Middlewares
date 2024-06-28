""" Middleware for handling request time calculation """

import time

from starlette.types import ASGIApp, Receive, Scope, Send, Message

from .utils import request_time_ctx_var


class RequestTimeMiddleware:  # pylint: disable=too-few-public-methods
    """Measure request time and store it in context variable"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        time_ref: float = time.perf_counter()

        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                request_time = time.perf_counter() - time_ref
                request_time_ctx_var.set(request_time)

            await send(message)

        await self.app(scope, receive, wrapped_send)
