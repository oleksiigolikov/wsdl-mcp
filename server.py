#!/usr/bin/env python3
"""
WSDL-Search MCP – Dynamically exposes every SOAP operation in the
given WSDL as an independent Fast-MCP tool.
"""
from __future__ import annotations

import asyncio
import functools
import logging
import os
import textwrap

from fast_mcp import MCPApp, Request, Response
from zeep import Client, helpers
from zeep.exceptions import Fault

from wsdl_utils import discover_operations, render_schema_md, coerce_inputs

log = logging.getLogger("wsdl_search_mcp")
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

WSDL_URL_ENV = "WSDL_URL"
EXEC_TIMEOUT = 5

app = MCPApp(title="WSDL-Search MCP")


def register_operation(op):
    """Register a SOAP operation as a Fast-MCP tool."""

    @app.tool(
        name=op.full_name,
        description=textwrap.dedent(
            f"""
            {op.doc or f"SOAP Operation **{op.operation}**."}
            {render_schema_md(op)}
            Input: JSON object where keys are parameter names shown above.
            Output: JSON object converted from the SOAP response.
            """
        ).strip(),
        input_schema="object",
        output_schema="any",
    )
    async def _(req: Request) -> Response:
        params: dict = req.json
        try:
            payload = coerce_inputs(op, params)
        except ValueError as exc:
            return Response(status=422, json={"error": str(exc)})

        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None, functools.partial(op.callable, **payload)
            )
        except Fault as fault:
            return Response(status=400, json={"fault": str(fault)})
        except Exception as exc:
            log.warning("soap-call-error %s: %s", op.full_name, exc)
            return Response(status=502, json={"error": str(exc)})

        return Response(json=helpers.serialize_object(result))


def startup():
    url = os.getenv(WSDL_URL_ENV)
    if not url:
        raise RuntimeError(f"{WSDL_URL_ENV} is not set")

    log.info("Loading WSDL %s", url)
    client = Client(url)

    for op in discover_operations(client):
        register_operation(op)
        log.info("Registered tool %s", op.full_name)


startup()
