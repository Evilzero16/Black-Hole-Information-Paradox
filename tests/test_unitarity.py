import numpy as np

from qiskit.quantum_info import Operator

from blackhole_paradox.circuits.scrambling import (
    build_black_hole_scrambler,
    build_inverse_scrambler,
)


def test_scrambler_inverse_matches_identity() -> None:
    n_qubits = 4
    depth = 3

    scrambler = build_black_hole_scrambler(n_qubits=n_qubits, depth=depth)
    inverse = build_inverse_scrambler(n_qubits=n_qubits, depth=depth)

    composed = scrambler.compose(inverse)
    unitary = Operator(composed).data
    identity = np.eye(2**n_qubits, dtype=complex)

    assert np.allclose(unitary, identity, atol=1e-8)
