"""Contains improved routing middleware for Connexion/Starlette."""

from typing import Optional, Dict, Any

import starlette
from connexion.middleware.routing import RoutingAPI, RoutingMiddleware
from connexion.spec import Specification
from starlette.routing import Route
from starlette.types import Receive, Scope, Send


class CustomRoutingMiddleware(  # pragma: no cover
    RoutingMiddleware  # type: ignore
):  # pylint: disable=too-few-public-methods
    """
    Adjusted Connexion Routing middleware that use CustomRoutingAPI
    instead of connexion RoutingAPI.
    """

    def add_api(
        self,
        specification: Specification,
        base_path: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:  # pragma: no cover
        """Add an API to the router based on a OpenAPI spec.

        Does exactly what parent func does, but the routes are sorted, because
        starlette iterates over routes and performs regex matching until a match is
        found. This means that more general routes might be matched before the specific
        variants, which is not what we want.

        Example:
        Incoming request on path:
        /registry/registry.com/repository/ubi8/python39/tag/tag1

        /registry/{registry}/repository/{repository}
            ^ if not correctly sorted this will get matched first,
              because repository is a path
        /registry/{registry}/repository/{repository}/tag/{tag}

        :param specification: OpenAPI spec.
        :param base_path: Base path where to add this API.
        :param arguments: Jinja arguments to replace in the spec.
        """
        api = RoutingAPI(
            specification,
            base_path=base_path,
            arguments=arguments,
            next_app=self.app,
            **kwargs,
        )

        routes_len = len(api.router.routes)

        def sorting_func(route: Route) -> int:
            """
            Sorts routing rules to avoid more general rules to be matched first.
            """

            # if path does not have any parameters, put it on top
            if not route.param_convertors:
                return routes_len + 1
            # otherwise use the length of the regex pattern
            return len(route.path_regex.pattern)

        api.router.routes.sort(key=sorting_func, reverse=True)

        # If an API with the same base_path was already registered, chain the new API
        # as its default. This way, if no matching route is found on the first API,
        # the request is forwarded to the new API.
        for route in self.router.routes:
            if (
                isinstance(route, starlette.routing.Mount)
                and route.path == api.base_path
            ):
                route.app.default = api.router  # type: ignore

        self.router.mount(api.base_path, app=api.router)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        scope["router"] = self.router
        return await super().__call__(scope, receive, send)
