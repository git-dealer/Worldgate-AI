from decimal import Decimal

from checks import weights_match


def test_equal_weights_match():
    assert weights_match(Decimal("1200"), Decimal("1200")) is True


def test_same_number_in_different_format_matches():
    assert weights_match(Decimal("1200"), Decimal("1200.00")) is True


def test_half_kg_difference_is_a_mismatch():
    assert weights_match(Decimal("1200"), Decimal("1199.5")) is False


def test_large_difference_is_a_mismatch():
    assert weights_match(Decimal("1200"), Decimal("1119.5")) is False