from collections import namedtuple
import importlib
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import wsdl_utils

OperationMeta = namedtuple(
    "OperationMeta", "service port operation full_name doc params callable"
)


def test_registration(monkeypatch):
    op = OperationMeta(
        service="Svc",
        port="Port",
        operation="Op",
        full_name="svc_port_op",
        doc="doc",
        params=[],
        callable=lambda **kw: None,
    )

    def fake_discover(client):
        return [op]

    monkeypatch.setattr(wsdl_utils, "discover_operations", fake_discover)
    import zeep
    monkeypatch.setattr(zeep, "Client", lambda url: object())
    monkeypatch.setenv("WSDL_URL", "dummy")
    import server
    importlib.reload(server)

    assert "svc_port_op" in server.app.tools
