import pytest

from core.patterns import segment_to_bytes


def test_fill_accepts_hex_prefixed_string():
    out = segment_to_bytes("fill", "0xAA", 4)
    assert out == b"\xAA" * 4


def test_fill_accepts_decimal_string():
    out = segment_to_bytes("fill", "170", 4)
    assert out == b"\xAA" * 4


def test_fill_accepts_binary_prefixed_string():
    out = segment_to_bytes("fill", "0b10101010", 4)
    assert out == b"\xAA" * 4


def test_fill_rejects_values_out_of_byte_range():
    with pytest.raises(ValueError, match="fill value must be 0..255"):
        segment_to_bytes("fill", "0x1FF", 4)
