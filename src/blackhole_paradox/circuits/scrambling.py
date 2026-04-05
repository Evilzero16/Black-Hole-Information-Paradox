from __future__ import annotations

from dataclasses import dataclass

from qiskit import QuantumCircuit

from blackhole_paradox.circuits.ansatz import build_scrambling_ansatz


@dataclass
class ScramblerMetadata:
    """
    Metadata describing the toy black-hole scrambler.
    """

    n_qubits: int
    depth: int
    gate_count: int
    operation_counts: dict[str, int]
    description: str


def build_black_hole_scrambler(n_qubits: int, depth: int) -> QuantumCircuit:
    """
    Build the toy black-hole scrambling unitary.

    This wraps the ansatz circuit and gives it a clearer semantic meaning
    in the context of the Hayden-Preskill-inspired demo.
    """
    qc = build_scrambling_ansatz(n_qubits=n_qubits, depth=depth)
    qc.name = "U_scramble"
    return qc


def build_inverse_scrambler(n_qubits: int, depth: int) -> QuantumCircuit:
    """
    Build the inverse of the scrambling circuit.

    In a realistic black-hole decoding story, recovery is subtle and depends
    on correlations and access to radiation. For a first toy demo, the inverse
    circuit provides a clean idealized reference for reconstruction.
    """
    scrambler = build_black_hole_scrambler(n_qubits=n_qubits, depth=depth)
    inverse = scrambler.inverse()
    inverse.name = "U_scramble_dg"
    return inverse


def scrambler_metadata(qc: QuantumCircuit, depth: int) -> ScramblerMetadata:
    """
    Extract frontend-friendly metadata for displaying the scrambling stage.
    """
    counts = qc.count_ops()
    operation_counts = {str(k): int(v) for k, v in counts.items()}

    return ScramblerMetadata(
        n_qubits=qc.num_qubits,
        depth=depth,
        gate_count=sum(operation_counts.values()),
        operation_counts=operation_counts,
        description=(
            "A toy scrambling circuit made of repeated single-qubit rotations "
            "and brickwork entangling layers. It spreads initially localized "
            "information across the black-hole register."
        ),
    )


def circuit_text_diagram(qc: QuantumCircuit) -> str:
    """
    Return a plain-text diagram for website/debug display.
    """
    return str(qc.draw(output="text"))


def build_scrambler_bundle(n_qubits: int, depth: int) -> dict:
    """
    Convenience helper returning everything needed for the scrambling stage.
    """
    qc = build_black_hole_scrambler(n_qubits=n_qubits, depth=depth)
    meta = scrambler_metadata(qc, depth=depth)

    return {
        "circuit": qc,
        "metadata": meta,
        "diagram": circuit_text_diagram(qc),
    }