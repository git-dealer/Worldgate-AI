from decimal import Decimal


def weights_match(invoice_kg: Decimal, packing_list_kg: Decimal) -> bool:
    return invoice_kg == packing_list_kg