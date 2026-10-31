from fastapi import FastAPI
from shipment import Shipment

app = FastAPI()

shipments = [
    shipment("S001", 1200, "booked"),
    shipment("S002", 2500, "in_transit"),
    shipment("S004", 3200, "delivered"),
]

@app.get("/")
def home():
    return {"message": "Worldgate API is running"}

@app.get("/shipments")
def list_shipments():
    return shipments

@app.get("/shipments/heavy")
def list_heavy_shipments():
    return [s for s in shipments if s.is_heavy()]

@app.get("/shipments/{shipment_id}")
def get_shipments(shipment_id: str)
    for s in shipments:
        if s.id == shipment_id:
            return s
    return {"error": "not found"}

@app.get("/shipments/status/{status}")
def get_shipments_by_status():
    return [s for s in shipments if s.status == status]


