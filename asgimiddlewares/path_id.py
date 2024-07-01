""" Middleware for handling path """

from starlette.types import ASGIApp, Receive, Scope, Send


class PathIdMiddleware:  # pylint: disable=too-few-public-methods
    """
    Update scope with path_id

    Needs to be positioned anywhere between the RoutingMiddleware
    and the ContextMiddleware to have access to the path_params
    provided by the RoutingMiddleware. Path_params are emptied
    during the response phase, so we cannot leverage
    the same logic as for logging and headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path_id: str = scope.get("path", "")
        if "path_params" in scope:
            for param_name, param_value in reversed(scope["path_params"].items()):
                string_param_value = str(param_value)
                endswith_param = path_id.endswith(string_param_value)
                pattern = "/" + string_param_value
                substitute = f"/<{param_name}>"

                if not endswith_param:
                    # Parameter is somewhere in the url and not at the end
                    pattern += "/"
                    substitute += "/"

                # Substitute the right-most occurrence
                left, right = path_id.rsplit(pattern, 1)
                path_id = substitute.join((left, right))

        scope["state"]["path_id"] = path_id

        await self.app(scope, receive, send)
