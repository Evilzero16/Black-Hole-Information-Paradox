from __future__ import annotations

from dataclasses import dataclass

from qiskit import QuantumCircuit


@dataclass
class EntanglementResource:
    """
    Describes the toy entanglement resource used in the black-hole demo.

    Registers are interpreted as:
    - reference: purifying partner / external reference system
    - black_hole: black hole degrees of freedom before message injection
    """

    reference_qubits: list[int]
    black_hole_qubits: list[int]
    num_pairs: int
    description: str


def create_bell_pair(qc: QuantumCircuit, q0: int, q1: int) -> None:
    """
    Create a Bell pair between q0 and q1:
        (|00> + |11>) / sqrt(2)
    """
    qc.h(q0)
    qc.cx(q0, q1)


def prepare_old_black_hole_entanglement(
    reference_size: int,
    black_hole_size: int,
) -> tuple[QuantumCircuit, EntanglementResource]:
    """
    Prepare a toy 'old black hole' entanglement resource.

    We entangle min(reference_size, black_hole_size) qubit pairs between:
    - an external reference register R
    - an initial black hole register B

    This captures the key Hayden-Preskill idea that an old black hole is
    already entangled with previously emitted radiation / an external purifier.

    Qubit layout in the returned circuit:
        [ R register | B register ]

    Returns:
        (circuit, metadata)
    """
    if not isinstance(reference_size, int) or reference_size <= 0:
        raise ValueError("reference_size must be a positive integer")

    if not isinstance(black_hole_size, int) or black_hole_size <= 0:
        raise ValueError("black_hole_size must be a positive integer")

    total_qubits = reference_size + black_hole_size
    qc = QuantumCircuit(total_qubits, name="BH_ent")

    reference_qubits = list(range(reference_size))
    black_hole_qubits = list(range(reference_size, total_qubits))

    num_pairs = min(reference_size, black_hole_size)

    for i in range(num_pairs):
        create_bell_pair(qc, reference_qubits[i], black_hole_qubits[i])

    resource = EntanglementResource(
        reference_qubits=reference_qubits,
        black_hole_qubits=black_hole_qubits,
        num_pairs=num_pairs,
        description=(
            "Prepared a toy old-black-hole resource by entangling the black-hole "
            "register with an external reference system."
        ),
    )

    return qc, resource


def entanglement_summary(reference_size: int, black_hole_size: int) -> dict:
    """
    Frontend-friendly summary of the initial entanglement resource.
    """
    _, resource = prepare_old_black_hole_entanglement(
        reference_size=reference_size,
        black_hole_size=black_hole_size,
    )

    return {
        "reference_qubits": resource.reference_qubits,
        "black_hole_qubits": resource.black_hole_qubits,
        "num_pairs": resource.num_pairs,
        "description": resource.description,
        "note": (
            "This models an 'old' black hole that is already entangled with an "
            "external system, which is central to Hayden-Preskill-style recovery."
        ),
    }


def circuit_text_diagram(qc: QuantumCircuit) -> str:
    """
    Return a plain-text circuit diagram for debugging or website display.
    """
    return str(qc.draw(output="text"))