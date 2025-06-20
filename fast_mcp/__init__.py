from __future__ import annotations
from typing import Callable, Any
from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse


class Request:
    def __init__(self, json: dict):
        self.json = json


class Response:
    def __init__(self, status: int = 200, json: Any | None = None):
        self.status = status
        self.json = json


class MCPApp:
    """Minimal MCP application wrapper using FastAPI."""

    def __init__(self, title: str = "Fast MCP"):
        self.app = FastAPI(title=title)
        self.tools: dict[str, Callable[[Request], Response]] = {}

    def tool(
        self,
        name: str,
        description: str = "",
        input_schema: str | None = None,
        output_schema: str | None = None,
    ) -> Callable[[Callable[[Request], Response]], Callable[[Request], Response]]:
        def decorator(func: Callable[[Request], Response]):
            self.tools[name] = func

            async def endpoint(request: FastAPIRequest):
                payload = await request.json()
                resp = await func(Request(payload))
                return JSONResponse(status_code=resp.status, content=resp.json)

            endpoint.__name__ = name.replace("-", "_")
            self.app.post(f"/invoke/{name}")(endpoint)
            return func

        return decorator
