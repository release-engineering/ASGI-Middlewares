""" Middleware for handling path """

import logging
from typing import Optional

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.routing import Router, Mount, Match, Route


LOG = logging.getLogger(__name__)


class PathIdMiddleware:  # pylint: disable=too-few-public-methods
    """
    Update scope with path_id

    Needs to be positioned after CustomRoutingMiddleware
    to have access to the router key provided by
    the middleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        router: Optional[Router] = scope.get("router")
        if not router:
            raise KeyError(
                "Scope does not contain the 'router' key. "
                "Make sure this middleware is placed right "
                "after CustomRoutingMiddleware!"
            )
        if scope.get("path") and scope.get("type") == "http" and router:
            for mount in router.routes:
                if scope.get("state", {}).get("path_id"):
                    break
                if not isinstance(mount, Mount):
                    continue
                if not isinstance(mount.app, Router):
                    continue

                match, child_scope = mount.matches(scope)
                if match != Match.FULL:
                    continue
                new_scope = {**scope, **child_scope}
                for route in mount.app.routes:
                    if not isinstance(route, Route):
                        continue
                    match, _ = route.matches(new_scope)

                    if match == Match.FULL:
                        scope["state"]["path_id"] = mount.path + route.path_format
                        break
            if not scope.get("state", {}).get("path_id"):
                # Not a part of application API, possibly swagger UI
                scope["state"]["path_id"] = ''
        await self.app(scope, receive, send)
