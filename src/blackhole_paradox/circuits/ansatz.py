from __future__ import annotations

from typing import Iterable

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector


def add_brickwork_entangling_layer(qc: QuantumCircuit, qubits: Iterable[int]) -> QuantumCircuit:
    """
    Add a simple nearest-neighbor brickwork entangling pattern.

    Example for qubits [0,1,2,3]:
    - even layer: CX(0,1), CX(2,3)
    - odd layer:  CX(1,2)

    This kind of layered local circuit is a standard toy model for scrambling.
    """
    qubits = list(qubits)
    n = len(qubits)

    if n < 2:
        return qc

    for start in (0, 1):
        for i in range(start, n - 1, 2):
            qc.cx(qubits[i], qubits[i + 1])

    return qc


def add_parameterized_single_qubit_layer(
    qc: QuantumCircuit,
    qubits: Iterable[int],
    theta_y: list[float] | None = None,
    theta_z: list[float] | None = None,
) -> QuantumCircuit:
    """
    Add a layer of single-qubit rotations.

    If theta_y/theta_z are not given, use fixed angles that still generate
    nontrivial dynamics suitable for a toy scrambling demo.
    """
    qubits = list(qubits)
    n = len(qubits)

    if theta_y is not None and len(theta_y) != n:
        raise ValueError("theta_y must match the number of qubits")

    if theta_z is not None and len(theta_z) != n:
        raise ValueError("theta_z must match the number of qubits")

    for i, q in enumerate(qubits):
        ry = theta_y[i] if theta_y is not None else 0.731
        rz = theta_z[i] if theta_z is not None else 0.413
        qc.ry(ry, q)
        qc.rz(rz, q)

    return qc


def build_scrambling_ansatz(n_qubits: int, depth: int) -> QuantumCircuit:
    """
    Build a deterministic toy scrambling circuit.

    Structure per layer:
    1. Single-qubit rotations
    2. Brickwork entangling pattern

    This is a good website/demo choice because:
    - it is reproducible
    - it spreads information across the register
    - it remains easy to visualize
    """
    if not isinstance(n_qubits, int) or n_qubits <= 0:
        raise ValueError("n_qubits must be a positive integer")

    if not isinstance(depth, int) or depth <= 0:
        raise ValueError("depth must be a positive integer")

    qc = QuantumCircuit(n_qubits, name="S")

    for layer in range(depth):
        theta_y = [0.731 + 0.07 * layer + 0.03 * q for q in range(n_qubits)]
        theta_z = [0.413 + 0.05 * layer + 0.02 * q for q in range(n_qubits)]
        add_parameterized_single_qubit_layer(qc, range(n_qubits), theta_y, theta_z)
        add_brickwork_entangling_layer(qc, range(n_qubits))

    return qc


def build_trainable_ansatz(n_qubits: int, depth: int) -> tuple[QuantumCircuit, ParameterVector]:
    """
    Optional trainable ansatz for later experiments.

    Returns:
        (circuit, parameters)

    This is useful if later you want to optimize a decoder or study
    variational scrambling/reconstruction.
    """
    if not isinstance(n_qubits, int) or n_qubits <= 0:
        raise ValueError("n_qubits must be a positive integer")

    if not isinstance(depth, int) or depth <= 0:
        raise ValueError("depth must be a positive integer")

    num_params = depth * n_qubits * 2
    params = ParameterVector("theta", length=num_params)

    qc = QuantumCircuit(n_qubits, name="A")

    idx = 0
    for _ in range(depth):
        for q in range(n_qubits):
            qc.ry(params[idx], q)
            idx += 1
            qc.rz(params[idx], q)
            idx += 1

        add_brickwork_entangling_layer(qc, range(n_qubits))

    return qc, params