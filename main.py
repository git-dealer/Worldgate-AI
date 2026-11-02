from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from checks import weights_match
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
    invoice_kg: float = Field(gt=0)
    packing_list_kg: float = Field(gt=0)
    tolerance_kg: float = Field(default=0.0, ge=0)


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
    match = weights_match(data.invoice_kg, data.packing_list_kg, data.tolerance_kg)
    difference = abs(data.invoice_kg - data.packing_list_kg)
    return {"match": match, "difference_kg": difference}
