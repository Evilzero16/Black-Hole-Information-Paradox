from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EncodedMessage:
    """
    Represents a short classical message encoded into a fixed-width bit block
    suitable for a toy quantum-information demo.

    In this project, the 'message' is a stand-in for a small quantum state
    that will be injected into a toy black-hole scrambling protocol.
    """

    original_message: str
    utf8_bits: str
    truncated_bits: str
    padded_bits: str
    message_qubits: int
    basis_index: int


def text_to_bits(message: str) -> str:
    """
    Convert a string to a UTF-8 bitstring.
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string")

    data = message.encode("utf-8")
    return "".join(f"{byte:08b}" for byte in data)


def bits_to_text(bits: str) -> str:
    """
    Convert a bitstring back to text.
    Length must be a multiple of 8.
    """
    validate_bitstring(bits)

    if len(bits) % 8 != 0:
        raise ValueError("bitstring length must be a multiple of 8")

    byte_values = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
    return bytes(byte_values).decode("utf-8", errors="strict")


def validate_bitstring(bits: str) -> None:
    """
    Ensure a string contains only 0 and 1.
    """
    if not isinstance(bits, str):
        raise TypeError("bitstring must be a string")

    if any(ch not in {"0", "1"} for ch in bits):
        raise ValueError("bitstring must contain only '0' and '1'")


def pad_or_truncate_bits(bits: str, width: int) -> tuple[str, str]:
    """
    Force a bitstring into a fixed width.

    Returns:
        (truncated_bits, padded_bits)

    Behavior:
    - If bits is longer than width, keep only the first `width` bits.
    - If bits is shorter than width, right-pad with zeros.
    """
    validate_bitstring(bits)

    if not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")

    truncated = bits[:width]
    padded = truncated.ljust(width, "0")
    return truncated, padded


def bitstring_to_int(bits: str) -> int:
    """
    Convert a bitstring to its integer basis-state index.
    """
    validate_bitstring(bits)

    if bits == "":
        raise ValueError("bitstring cannot be empty")

    return int(bits, 2)


def int_to_bitstring(value: int, width: int) -> str:
    """
    Convert an integer to a zero-padded bitstring of a given width.
    """
    if not isinstance(value, int) or value < 0:
        raise ValueError("value must be a non-negative integer")

    if not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")

    if value >= 2 ** width:
        raise ValueError(f"value {value} does not fit in {width} bits")

    return format(value, f"0{width}b")


def encode_message_for_register(message: str, message_qubits: int) -> EncodedMessage:
    """
    Encode a short user message into a fixed-size bit block corresponding
    to a computational-basis state on `message_qubits` qubits.

    This is a toy encoding for the website demo:
    - message -> UTF-8 bits
    - fit into message_qubits bits
    - interpret as a basis index

    Example:
        message_qubits = 4
        'A' -> UTF-8 bits 01000001
        truncated to 0100
        basis index = 4
    """
    if not isinstance(message_qubits, int) or message_qubits <= 0:
        raise ValueError("message_qubits must be a positive integer")

    utf8_bits = text_to_bits(message)
    truncated_bits, padded_bits = pad_or_truncate_bits(utf8_bits, message_qubits)
    basis_index = bitstring_to_int(padded_bits)

    return EncodedMessage(
        original_message=message,
        utf8_bits=utf8_bits,
        truncated_bits=truncated_bits,
        padded_bits=padded_bits,
        message_qubits=message_qubits,
        basis_index=basis_index,
    )


def decode_register_bits_to_message(bits: str) -> str:
    """
    Decode a recovered bitstring back into text where possible.

    Because the toy protocol may only preserve a small fixed-width block,
    this function is mainly useful for demo reconstruction when the bitstring
    length is a multiple of 8.

    If not divisible by 8, the raw bitstring should be shown directly in the UI.
    """
    validate_bitstring(bits)

    if len(bits) % 8 != 0:
        raise ValueError(
            "Recovered bitstring length is not a multiple of 8, "
            "so it cannot be decoded directly to UTF-8 text."
        )

    return bits_to_text(bits)


def encoding_summary(message: str, message_qubits: int) -> dict:
    """
    Return a frontend-friendly summary of the encoding stage.
    """
    encoded = encode_message_for_register(message, message_qubits)

    return {
        "original_message": encoded.original_message,
        "utf8_bits": encoded.utf8_bits,
        "truncated_bits": encoded.truncated_bits,
        "padded_bits": encoded.padded_bits,
        "message_qubits": encoded.message_qubits,
        "basis_index": encoded.basis_index,
        "basis_label": f"|{encoded.padded_bits}>",
        "note": (
            "This is a toy encoding into a computational basis state for a small "
            "quantum register, used to demonstrate scrambling and recovery."
        ),
    }