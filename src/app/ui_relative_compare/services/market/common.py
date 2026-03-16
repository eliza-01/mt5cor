MIN_ORDER_LOTS = 0.01


def pip_size_from_digits(digits: int) -> float:
    return 0.01 if digits in (2, 3) else 0.0001
