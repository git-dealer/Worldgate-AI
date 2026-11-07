from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

import db
from checks import weights_match
from doc_checks import DocFields, find_mismatches, find_missing_fields
from shipment import Shipment

app = FastAPI(title="Worldgate API")

shipments = [
    Shipment("S001", 1200, "booked"),
    Shipment("S002", 2500, "in_transit"),
    Shipment("S004", 3200, "delivered"),
]


class ShipmentIn(BaseModel):
    id: str
    weight: float = Field(gt=0)
    status: str


class WeightCheckIn(BaseModel):
    invoice_kg: Decimal = Field(gt=0)
    packing_list_kg: Decimal = Field(gt=0)


EXAMPLE_REQUEST = {
    "commercial_invoice": {
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
    },
    "bill_of_lading": {
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
        "gross_weight_kg": 479.5,
        "net_weight_kg": 450,
    },
}


class CheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [EXAMPLE_REQUEST]})

    commercial_invoice: DocFields | None = None
    packing_list: DocFields | None = None
    invoice_packing_list: DocFields | None = None
    bill_of_lading: DocFields | None = None


@app.get("/")
def home():
    return {"message": "Worldgate API is running"}


@app.get("/shipments")
def list_shipments():
    return shipments


@app.get("/shipments/heavy")
def list_heavy_shipments():
    return [s for s in shipments if s.is_heavy()]


@app.get("/shipments/status/{status}")
def get_shipments_by_status(status: str):
    return [s for s in shipments if s.status == status]


@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str):
    for s in shipments:
        if s.id == shipment_id:
            return s
    raise HTTPException(status_code=404, detail="shipment not found")


@app.post("/shipments", status_code=201)
def create_shipment(item: ShipmentIn):
    for s in shipments:
        if s.id == item.id:
            raise HTTPException(status_code=409, detail="shipment id already exists")
    new_shipment = Shipment(item.id, item.weight, item.status)
    shipments.append(new_shipment)
    return new_shipment


@app.post("/check/weights")
def check_weights(data: WeightCheckIn):
    match = weights_match(data.invoice_kg, data.packing_list_kg)
    difference = abs(data.invoice_kg - data.packing_list_kg)
    return {"match": match, "difference_kg": str(difference)}


@app.post("/check/documents")
def check_documents(request: CheckRequest):
    docs = {
        name: getattr(request, name)
        for name in CheckRequest.model_fields
        if getattr(request, name) is not None
    }
    if not docs:
        raise HTTPException(status_code=400, detail="send at least one document")

    mismatches = find_mismatches(docs)
    missing = find_missing_fields(docs)

    if mismatches or missing:
        result = "issues found"
    elif len(docs) < 2:
        result = "completeness checked only; send two or more documents to compare them"
    else:
        result = "no issues in the fields checked"

    check_id = db.save_check(list(docs.keys()), mismatches, missing, result)

    return {
        "check_id": check_id,
        "documents_checked": list(docs.keys()),
        "mismatches": mismatches,
        "missing_fields": missing,
        "result": result,
    }


@app.get("/checks")
def list_saved_checks():
    return db.list_checks()


@app.get("/checks/{check_id}")
def get_saved_check(check_id: int):
    check = db.get_check(check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="check not found")
    return check