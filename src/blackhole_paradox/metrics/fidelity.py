from __future__ import annotations

from typing import Sequence

import numpy as np


def bitwise_accuracy(original_bits: str, recovered_bits: str) -> float:
    """
    Compute the fraction of matching bits between two bitstrings.

    If lengths differ, comparison is performed on the overlapping prefix.
    """
    _validate_bitstring(original_bits)
    _validate_bitstring(recovered_bits)

    if len(original_bits) == 0 and len(recovered_bits) == 0:
        return 1.0

    overlap = min(len(original_bits), len(recovered_bits))
    if overlap == 0:
        return 0.0

    matches = sum(
        1 for a, b in zip(original_bits[:overlap], recovered_bits[:overlap]) if a == b
    )
    return matches / overlap


def exact_match_success(original_bits: str, recovered_bits: str) -> float:
    """
    Return 1.0 if the bitstrings match exactly, else 0.0.
    """
    _validate_bitstring(original_bits)
    _validate_bitstring(recovered_bits)
    return 1.0 if original_bits == recovered_bits else 0.0


def computational_basis_fidelity(original_bits: str, recovered_bits: str) -> float:
    """
    Fidelity for computational basis states.

    Since your demo encodes the message into a basis-state block, the state
    fidelity is 1 if the recovered basis label matches exactly, else 0.
    """
    _validate_bitstring(original_bits)
    _validate_bitstring(recovered_bits)

    if len(original_bits) != len(recovered_bits):
        return 0.0

    return 1.0 if original_bits == recovered_bits else 0.0


def statevector_fidelity(
    psi: Sequence[complex] | np.ndarray,
    phi: Sequence[complex] | np.ndarray,
) -> float:
    """
    Compute pure-state fidelity F = |<psi|phi>|^2 for two statevectors.
    """
    psi_arr = np.asarray(psi, dtype=complex)
    phi_arr = np.asarray(phi, dtype=complex)

    if psi_arr.ndim != 1 or phi_arr.ndim != 1:
        raise ValueError("psi and phi must be 1D statevectors")

    if psi_arr.shape != phi_arr.shape:
        raise ValueError("psi and phi must have the same shape")

    psi_norm = np.linalg.norm(psi_arr)
    phi_norm = np.linalg.norm(phi_arr)

    if psi_norm == 0 or phi_norm == 0:
        raise ValueError("statevectors must be non-zero")

    psi_arr = psi_arr / psi_norm
    phi_arr = phi_arr / phi_norm

    overlap = np.vdot(psi_arr, phi_arr)
    return float(np.abs(overlap) ** 2)


def fidelity_summary(original_bits: str, recovered_bits: str) -> dict:
    """
    Frontend- and protocol-friendly summary of recovery quality.

    For the current toy model, 'fidelity' is the computational-basis fidelity.
    """
    return {
        "fidelity": computational_basis_fidelity(original_bits, recovered_bits),
        "success_probability": exact_match_success(original_bits, recovered_bits),
        "bitwise_accuracy": bitwise_accuracy(original_bits, recovered_bits),
    }


def _validate_bitstring(bits: str) -> None:
    if not isinstance(bits, str):
        raise TypeError("bitstring must be a string")

    if any(ch not in {"0", "1"} for ch in bits):
        raise ValueError("bitstring must contain only '0' and '1'")