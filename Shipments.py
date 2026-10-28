
import json


def find_heaviest(shipments):
    return max(shipments, key=lambda s: s["weight"])


def total_weight(shipments):
    total = 0
    for shipment in shipments:
        total += shipment["weight"]
    return total


def filter_by_origin(shipments, city):
    return [
        shipment for shipment in shipments
        if shipment["origin"].lower() == city.lower()
    ]


def count_by_status(shipments):
    counts = {
        "booked": 0,
        "in_transit": 0,
        "delivered": 0
    }

    for shipment in shipments:
        status = shipment["status"].lower()
        if status in counts:
            counts[status] += 1

    return counts


shipments = [
    {"id": "S001", "origin": "Chennai", "destination": "Dubai",
     "weight": 1200, "status": "booked"},

    {"id": "S002", "origin": "Mumbai", "destination": "Singapore",
     "weight": 2500, "status": "in_transit"},

    {"id": "S003", "origin": "Delhi", "destination": "London",
     "weight": 1800, "status": "in_transit"},

    {"id": "S004", "origin": "Hyderabad", "destination": "New York",
     "weight": 3200, "status": "delivered"},

    {"id": "S005", "origin": "Kolkata", "destination": "Tokyo",
     "weight": 900, "status": "delivered"}
]


if __name__ == "__main__":

    # 1. Find the heaviest shipment
    heaviest = find_heaviest(shipments)
    print(
        f"Heaviest: {heaviest['id']} "
        f"({heaviest['origin']} → {heaviest['destination']}, "
        f"{heaviest['weight']} kg)"
    )

    # 2. Calculate total shipment weight
    print("Total weight:", total_weight(shipments), "kg")

    # 3. Filter shipments by origin
    print("Shipments from Hyderabad:")
    for shipment in filter_by_origin(shipments, "Hyderabad"):
        print(shipment)

    # 4. Count shipments by status
    print("Shipment counts by status:")
    print(count_by_status(shipments))

    # 5. Save shipments to JSON
    with open("shipments.json", "w", encoding="utf-8") as file:
        json.dump(shipments, file, indent=4)

    # 6. Read shipments from JSON
    with open("shipments.json", "r", encoding="utf-8") as file:
        loaded_shipments = json.load(file)

    print("Shipments loaded from shipments.json:")
    print(json.dumps(loaded_shipments, indent=4))

    print("Powered by Worldgate AI")

