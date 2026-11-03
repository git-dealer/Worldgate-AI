import pytest
from fastapi.testclient import TestClient

import db
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    # every test gets its own empty database, so real data is never touched
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))


def invoice(**overrides):
    base = {
        "shipper_name": "ABC Exports Pvt Ltd",
        "shipper_address": "Plot 12, Road No 5, Hyderabad, India",
        "consignee_name": "Gulf Trading LLC",
        "consignee_address": "Warehouse 7, Jebel Ali Free Zone, Dubai, UAE",
        "consignee_country": "UAE",
        "invoice_number": "INV-101",
        "invoice_date": "2026-11-03",
        "goods_description": "Cotton t-shirts, style TS-100",
        "hs_code": "61091000",
        "total_value": 12000,
        "currency": "USD",
        "incoterm": "FOB",
        "shipping_method": "Sea",
        "carrier_name": "Sample Shipping Line",
        "shipping_date": "2026-11-20",
        "bank_details_present": True,
        "number_of_packages": 40,
        "gross_weight_kg": 480,
        "net_weight_kg": 450,
    }
    base.update(overrides)
    return base


def bl(**overrides):
    base = {
        "shipper_name": "ABC Exports Pvt Ltd",
        "shipper_address": "Plot 12, Road No 5, Hyderabad, India",
        "consignee_name": "Gulf Trading LLC",
        "consignee_address": "Warehouse 7, Jebel Ali Free Zone, Dubai, UAE",
        "carrier_name": "Sample Shipping Line",
        "carrier_address": "1 Harbour Road, Mumbai, India",
        "goods_description": "40 cartons cotton t-shirts, HS 6109.10",
        "hs_code": "6109.10",
        "number_of_packages": 40,
        "incoterm": "FOB",
        "gross_weight_kg": 480,
        "net_weight_kg": 450,
    }
    base.update(overrides)
    return base


def test_home_returns_message():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Worldgate API is running"}


def test_matching_documents_have_no_issues():
    response = client.post(
        "/check/documents",
        json={"commercial_invoice": invoice(), "bill_of_lading": bl()},
    )
    assert response.status_code == 200
    assert response.json()["mismatches"] == []
    assert response.json()["result"] == "no issues in the fields checked"


def test_weight_mismatch_is_reported():
    response = client.post(
        "/check/documents",
        json={"commercial_invoice": invoice(), "bill_of_lading": bl(gross_weight_kg=479.5)},
    )
    body = response.json()
    assert response.status_code == 200
    assert len(body["mismatches"]) == 1
    assert "gross_weight_kg" in body["mismatches"][0]
    assert body["result"] == "issues found"


def test_missing_field_is_reported():
    response = client.post(
        "/check/documents",
        json={"commercial_invoice": invoice(consignee_address=None), "bill_of_lading": bl()},
    )
    assert "commercial_invoice: missing consignee_address" in response.json()["missing_fields"]


def test_unknown_document_type_returns_400():
    response = client.post(
        "/check/documents",
        json={"commercial_invoice": invoice(), "bol": bl()},
    )
    assert response.status_code == 400


def test_net_weight_above_gross_returns_422():
    response = client.post(
        "/check/documents",
        json={"commercial_invoice": invoice(), "bill_of_lading": bl(net_weight_kg=500)},
    )
    assert response.status_code == 422


def test_check_is_saved_and_can_be_read_back():
    created = client.post(
        "/check/documents",
        json={"commercial_invoice": invoice(), "bill_of_lading": bl(gross_weight_kg=479.5)},
    ).json()

    saved = client.get(f"/checks/{created['check_id']}")
    assert saved.status_code == 200
    assert saved.json()["result"] == "issues found"

    history = client.get("/checks").json()
    assert len(history) == 1
    assert history[0]["mismatch_count"] == 1


def test_unknown_check_id_returns_404():
    assert client.get("/checks/9999").status_code == 404