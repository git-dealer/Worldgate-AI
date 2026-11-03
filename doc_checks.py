import re
from datetime import date
from decimal import Decimal
from itertools import combinations
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # parties
    shipper_name: str | None = None
    shipper_address: str | None = None
    consignee_name: str | None = None
    consignee_address: str | None = None
    consignee_country: str | None = None
    carrier_name: str | None = None
    carrier_address: str | None = None

    # invoice details
    invoice_number: str | None = None
    invoice_date: date | None = None
    total_value: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    incoterm: Literal[
        "EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"
    ] | None = None
    shipping_method: str | None = None
    shipping_date: date | None = None
    bank_details_present: bool | None = None

    # goods
    goods_description: str | None = None
    hs_code: str | None = Field(default=None, pattern=r"^\d{4}\.?\d{2}(\.?\d{2,4})?$")
    number_of_packages: int | None = Field(default=None, gt=0)
    gross_weight_kg: Decimal | None = Field(default=None, gt=0)
    net_weight_kg: Decimal | None = Field(default=None, gt=0)
    dimensions: str | None = None

    @model_validator(mode="after")
    def net_not_more_than_gross(self):
        if self.gross_weight_kg is not None and self.net_weight_kg is not None:
            if self.net_weight_kg > self.gross_weight_kg:
                raise ValueError("net weight cannot be more than gross weight")
        return self


# Fields compared across documents. goods_description and dimensions are not compared yet.
COMPARED_FIELDS = [
    "shipper_name", "shipper_address", "consignee_name", "consignee_address",
    "consignee_country", "carrier_name", "carrier_address",
    "invoice_number", "invoice_date", "total_value", "currency", "incoterm",
    "hs_code", "number_of_packages", "gross_weight_kg", "net_weight_kg",
]

# For these, capitals, punctuation and extra spaces don't count as differences.
TEXT_FIELDS = {
    "shipper_name", "shipper_address", "consignee_name", "consignee_address",
    "consignee_country", "carrier_name", "carrier_address",
}

_INVOICE = [
    "shipper_name", "shipper_address", "consignee_name", "consignee_address",
    "consignee_country", "invoice_number", "invoice_date", "goods_description",
    "hs_code", "total_value", "currency", "incoterm", "shipping_method",
    "carrier_name", "shipping_date", "bank_details_present",
]
_PACKING = [
    "shipper_name", "consignee_name", "goods_description",
    "number_of_packages", "gross_weight_kg", "net_weight_kg", "dimensions",
]
_BL = [
    "shipper_name", "shipper_address", "consignee_name", "consignee_address",
    "carrier_name", "carrier_address", "goods_description",
    "number_of_packages", "incoterm", "gross_weight_kg", "net_weight_kg",
]

REQUIRED_FIELDS = {
    "commercial_invoice": _INVOICE,
    "packing_list": _PACKING,
    "invoice_packing_list": sorted(set(_INVOICE + _PACKING)),
    "bill_of_lading": _BL,
}


def normalize_text(text: str) -> str:
    # lowercase; turn punctuation and repeated spaces into single spaces
    return re.sub(r"[\W_]+", " ", text.casefold()).strip()


def digits_only(code: str) -> str:
    return re.sub(r"\D", "", code)


def values_agree(field_name: str, a, b) -> bool:
    if field_name in TEXT_FIELDS:
        return normalize_text(a) == normalize_text(b)
    if field_name == "hs_code":
        a, b = digits_only(a), digits_only(b)
        return a.startswith(b) or b.startswith(a)
    return a == b


def find_mismatches(docs: dict[str, DocFields]) -> list[str]:
    messages = []
    for field_name in COMPARED_FIELDS:
        values = {}
        for doc_name, doc in docs.items():
            value = getattr(doc, field_name)
            if value is not None:
                values[doc_name] = value

        for (_, a), (_, b) in combinations(values.items(), 2):
            if not values_agree(field_name, a, b):
                details = ", ".join(f"{doc}={val}" for doc, val in values.items())
                messages.append(f"{field_name} differs: {details}")
                break
    return messages


def find_missing_fields(docs: dict[str, DocFields]) -> list[str]:
    messages = []
    for doc_name, doc in docs.items():
        for field_name in REQUIRED_FIELDS.get(doc_name, []):
            value = getattr(doc, field_name)
            if value is None or value is False:
                messages.append(f"{doc_name}: missing {field_name}")
    return messages