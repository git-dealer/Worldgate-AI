from checks import weights_match


def test_equal_weights_match():
    assert weights_match(1200, 1200) is True


def test_different_weights_do_not_match():
    assert weights_match(1200, 1150) is False


def test_within_tolerance_matches():
    assert weights_match(1200, 1199.5, tolerance_kg=1) is True


def test_outside_tolerance_does_not_match():
    assert weights_match(1200, 1190, tolerance_kg=1) is False