"""
Entrypoint alias for Render / ASGI deployment.
Exposes the FastAPI `app` instance from server.py.
"""
from server import app

__all__ = ["app"]
