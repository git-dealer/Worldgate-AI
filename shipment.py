from dataclasses import dataclass

@dataclass
class Shipment:
    id:str
    weight:float
    status:str
    
    def __post_init__(self):
        if self.weight <= 0:
            raise ValueError("Weight must be positive")
        
    def is_heavy(self):
        return self.weight > 2000
    
    def is_delivered(self):
        return self.status == "delivered"
    
s1 = Shipment("S001", 1200, "delivered")
s4 = Shipment("s004", 3200, "in_transit")

print(s1.is_heavy())
print(s4.is_heavy())
print(s1.is_delivered())
print(s4.is_delivered())

if __name__ == "__main__":
    bad = Shipment("S999", 0, "booked")
