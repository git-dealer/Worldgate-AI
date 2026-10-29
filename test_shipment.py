import pytest
from shipment import Shipment


def test_is_heavy_true():
    assert Shipment("S001", 1500, "booked").is_heavy() is True
    
    
def test_is_heavy_false():    
    assert Shipment("S002", 1800, "booked").is_heavy() is False
    
    
def test_negative_weight_raises():
    with pytest.raises(ValueError):
        Shipment("S999", -5, "booked")  
    
    
#     Shipment("S999", -5, "booked")