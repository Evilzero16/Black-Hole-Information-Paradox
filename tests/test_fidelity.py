import numpy as np
import pytest

from blackhole_paradox.metrics.fidelity import (
    bitwise_accuracy,
    computational_basis_fidelity,
    exact_match_success,
    fidelity_summary,
    statevector_fidelity,
)


def test_bitwise_accuracy_overlap_behavior() -> None:
    assert bitwise_accuracy("1010", "1011") == 0.75
    assert bitwise_accuracy("1010", "10") == 1.0
    assert bitwise_accuracy("", "") == 1.0
    assert bitwise_accuracy("1", "") == 0.0


def test_exact_and_basis_fidelity() -> None:
    assert exact_match_success("101", "101") == 1.0
    assert exact_match_success("101", "001") == 0.0
    assert computational_basis_fidelity("0101", "0101") == 1.0
    assert computational_basis_fidelity("0101", "0100") == 0.0
    assert computational_basis_fidelity("0101", "010") == 0.0


def test_statevector_fidelity_for_known_states() -> None:
    zero = np.array([1.0, 0.0], dtype=complex)
    one = np.array([0.0, 1.0], dtype=complex)
    plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)

    assert statevector_fidelity(zero, zero) == pytest.approx(1.0)
    assert statevector_fidelity(zero, one) == pytest.approx(0.0)
    assert statevector_fidelity(zero, plus) == pytest.approx(0.5)


def test_fidelity_summary_fields() -> None:
    summary = fidelity_summary("1100", "1110")
    assert set(summary.keys()) == {"fidelity", "success_probability", "bitwise_accuracy"}
    assert summary["fidelity"] == 0.0
    assert summary["success_probability"] == 0.0
    assert summary["bitwise_accuracy"] == pytest.approx(0.75)
