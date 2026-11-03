from decimal import Decimal
import db
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from checks import weights_match
from doc_checks import REQUIRED_FIELDS, DocFields, find_mismatches, find_missing_fields
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
def check_documents(docs: dict[str, DocFields]):
    unknown = [name for name in docs if name not in REQUIRED_FIELDS]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"unknown document type {unknown}. Use: {list(REQUIRED_FIELDS)}",
        )

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
