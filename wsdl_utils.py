from __future__ import annotations
import textwrap
from collections import namedtuple
from typing import Any
from zeep import helpers, xsd

OperationMeta = namedtuple(
    "OperationMeta",
    "service port operation full_name doc params callable",
)


def discover_operations(client) -> list[OperationMeta]:
    meta: list[OperationMeta] = []
    for service in client.wsdl.services.values():
        for port in service.ports.values():
            binding = port.binding
            for op_name, op_obj in binding._operations.items():
                signature = op_obj.input.body.type
                params = _flatten_signature(signature)
                full = f"{service.name}_{port.name}_{op_name}".lower()
                meta.append(
                    OperationMeta(
                        service=service.name,
                        port=port.name,
                        operation=op_name,
                        full_name=full,
                        doc=op_obj.operation.input.documentation,
                        params=params,
                        callable=getattr(client.service, op_name),
                    )
                )
    return meta


def render_schema_md(op: OperationMeta) -> str:
    lines = ["Parameters:"]
    for p in op.params:
        annot = f"{p['type']}{' (optional)' if p['optional'] else ''}"
        lines.append(f"  • **{p['name']}** – {annot}")
        if p.get("children"):
            for child in p["children"]:
                lines.append(f"      • {child['name']} ({child['type']})")
    return textwrap.indent("\n".join(lines), "")


def _flatten_signature(sig) -> list[dict]:
    params = []
    for element in sig.elements:
        children = []
        if isinstance(element.type, xsd.ComplexType):
            for sub in element.type.elements:
                children.append(
                    dict(
                        name=sub.name,
                        type=sub.type.name,
                        optional=sub.min_occurs == 0,
                    )
                )
        params.append(
            dict(
                name=element.name,
                type=element.type.name,
                optional=element.min_occurs == 0,
                children=children or None,
            )
        )
    return params


def coerce_inputs(op: OperationMeta, payload: dict):
    result = {}
    for p in op.params:
        name = p["name"]
        if name not in payload:
            if p["optional"]:
                continue
            raise ValueError(f"missing required field '{name}'")
        result[name] = payload[name]
    return result
