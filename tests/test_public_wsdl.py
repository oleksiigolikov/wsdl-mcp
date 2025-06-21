import importlib
from fastapi.testclient import TestClient


def _load_server(url):
    import os
    os.environ['WSDL_URL'] = url
    import server
    return importlib.reload(server)


def test_calculator_add(monkeypatch):
    server = _load_server('http://www.dneonline.com/calculator.asmx?WSDL')
    client = TestClient(server.app.app)
    resp = client.post('/invoke/calculator_calculatorsoap_add', json={'intA': 2, 'intB': 3})
    assert resp.status_code == 200
    assert resp.json() == 5


def test_number_conversion(monkeypatch):
    server = _load_server('https://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL')
    client = TestClient(server.app.app)
    resp = client.post('/invoke/numberconversion_numberconversionsoap_numbertowords', json={'ubiNum': 5})
    assert resp.status_code == 200
    assert resp.json().strip() == 'five'


def test_hello(monkeypatch):
    server = _load_server('https://apps.learnwebservices.com/services/hello?WSDL')
    client = TestClient(server.app.app)
    resp = client.post('/invoke/helloendpointservice_helloendpointport_sayhello', json={'Name': 'Bob'})
    assert resp.status_code == 200
    assert resp.json() == 'Hello Bob!'
