"""Luhn (mod-10) helpers for building/validating card numbers in tests."""


def luhn_checksum(number: str) -> int:
    digits = [int(d) for d in number if d.isdigit()]
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd)
    for d in even:
        total += sum(divmod(d * 2, 10))
    return total % 10


def is_luhn_valid(number: str) -> bool:
    return luhn_checksum(number) == 0


def make_luhn_invalid(number: str) -> str:
    """Flip the last digit so the number fails the Luhn check."""
    last = int(number[-1])
    bad = (last + 1) % 10
    return number[:-1] + str(bad)