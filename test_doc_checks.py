from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from doc_checks import DocFields, find_mismatches, find_missing_fields


def make_invoice(**overrides):
    base = dict(
        shipper_name="ABC Exports Pvt Ltd",
        shipper_address="Plot 12, Road No 5, Hyderabad, India",
        consignee_name="Gulf Trading LLC",
        consignee_address="Warehouse 7, Jebel Ali Free Zone, Dubai, UAE",
        consignee_country="UAE",
        invoice_number="INV-101",
        invoice_date=date(2026, 11, 3),
        goods_description="Cotton t-shirts, style TS-100",
        hs_code="61091000",
        total_value=Decimal("12000"),
        currency="USD",
        incoterm="FOB",
        shipping_method="Sea",
        carrier_name="Sample Shipping Line",
        shipping_date=date(2026, 11, 20),
        bank_details_present=True,
        number_of_packages=40,
        gross_weight_kg=Decimal("480"),
        net_weight_kg=Decimal("450"),
    )
    base.update(overrides)
    return DocFields(**base)


def make_bl(**overrides):
    base = dict(
        shipper_name="ABC Exports Pvt Ltd",
        shipper_address="Plot 12, Road No 5, Hyderabad, India",
        consignee_name="Gulf Trading LLC",
        consignee_address="Warehouse 7, Jebel Ali Free Zone, Dubai, UAE",
        carrier_name="Sample Shipping Line",
        carrier_address="1 Harbour Road, Mumbai, India",
        goods_description="40 cartons cotton t-shirts, HS 6109.10",
        hs_code="6109.10",
        number_of_packages=40,
        incoterm="FOB",
        gross_weight_kg=Decimal("480"),
        net_weight_kg=Decimal("450"),
    )
    base.update(overrides)
    return DocFields(**base)


def test_matching_invoice_and_bl_have_no_mismatches():
    docs = {"commercial_invoice": make_invoice(), "bill_of_lading": make_bl()}
    assert find_mismatches(docs) == []


def test_name_formatting_differences_are_ignored():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(shipper_name="ABC EXPORTS PVT. LTD."),
    }
    assert find_mismatches(docs) == []


def test_different_consignee_name_is_caught():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(consignee_name="Gulf Trading LLP"),
    }
    result = find_mismatches(docs)
    assert len(result) == 1
    assert "consignee_name" in result[0]


def test_half_kg_gross_weight_difference_is_caught():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(gross_weight_kg=Decimal("479.5")),
    }
    result = find_mismatches(docs)
    assert len(result) == 1
    assert "gross_weight_kg" in result[0]


def test_package_count_difference_is_caught():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(number_of_packages=41),
    }
    result = find_mismatches(docs)
    assert len(result) == 1
    assert "number_of_packages" in result[0]


def test_hs_codes_with_different_last_digits_are_caught():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(hs_code="6109.10.90"),
    }
    result = find_mismatches(docs)
    assert len(result) == 1
    assert "hs_code" in result[0]


def test_hs_codes_from_different_chapters_are_caught():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(hs_code="6110.20"),
    }
    result = find_mismatches(docs)
    assert len(result) == 1
    assert "hs_code" in result[0]


def test_weight_on_only_one_document_is_skipped():
    docs = {
        "commercial_invoice": make_invoice(),
        "bill_of_lading": make_bl(gross_weight_kg=None, net_weight_kg=None),
    }
    assert find_mismatches(docs) == []


def test_net_weight_above_gross_weight_is_rejected():
    with pytest.raises(ValidationError):
        make_bl(net_weight_kg=Decimal("500"))


def test_seven_digit_hs_code_is_rejected():
    with pytest.raises(ValidationError):
        make_bl(hs_code="6109100")


def test_complete_documents_have_nothing_missing():
    docs = {"commercial_invoice": make_invoice(), "bill_of_lading": make_bl()}
    assert find_missing_fields(docs) == []


def test_missing_consignee_address_is_reported():
    docs = {"bill_of_lading": make_bl(consignee_address=None)}
    assert find_missing_fields(docs) == ["bill_of_lading: missing consignee_address"]


def test_bank_details_shown_as_false_counts_as_missing():
    docs = {"commercial_invoice": make_invoice(bank_details_present=False)}
    assert find_missing_fields(docs) == ["commercial_invoice: missing bank_details_present"]