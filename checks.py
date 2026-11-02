def weights_match(invoice_kg: float, packing_list_kg: float, tolerance_kg: float = 0.0) -> bool:
    return abs(invoice_kg - packing_list_kg) <= tolerance_kg