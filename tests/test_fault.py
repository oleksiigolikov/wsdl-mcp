from collections import namedtuple
import importlib
from fastapi.testclient import TestClient
from zeep.exceptions import Fault
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import wsdl_utils

OperationMeta = namedtuple(
    "OperationMeta", "service port operation full_name doc params callable"
)


def test_fault(monkeypatch):
    def handler(**params):
        raise Fault("boom")

    op = OperationMeta(
        service="Svc",
        port="Port",
        operation="Op",
        full_name="svc_port_op",
        doc="doc",
        params=[{"name": "x", "type": "int", "optional": False, "children": None}],
        callable=handler,
    )

    def fake_discover(client):
        return [op]

    monkeypatch.setattr(wsdl_utils, "discover_operations", fake_discover)
    import zeep
    monkeypatch.setattr(zeep, "Client", lambda url: object())
    monkeypatch.setenv("WSDL_URL", "dummy")
    import server
    importlib.reload(server)

    client = TestClient(server.app.app)
    resp = client.post("/invoke/svc_port_op", json={"x": 1})
    assert resp.status_code == 400
    assert resp.json() == {"fault": "boom"}
