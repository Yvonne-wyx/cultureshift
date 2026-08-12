"""CultureShift MVP backend foundation."""

from typing import Any

__all__ = ["app", "create_app"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from cultureshift.app import app, create_app

        return {"app": app, "create_app": create_app}[name]
    raise AttributeError(name)
