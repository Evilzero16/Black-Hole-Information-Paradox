from __future__ import annotations

from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error


def build_depolarizing_noise_model(
    p1: float = 0.001,
    p2: float = 0.01,
) -> NoiseModel:
    """
    Build a simple depolarizing noise model.

    Parameters:
    - p1: single-qubit depolarizing probability
    - p2: two-qubit depolarizing probability
    """
    if not (0.0 <= p1 <= 1.0):
        raise ValueError("p1 must be between 0 and 1")

    if not (0.0 <= p2 <= 1.0):
        raise ValueError("p2 must be between 0 and 1")

    noise_model = NoiseModel()

    error_1q = depolarizing_error(p1, 1)
    error_2q = depolarizing_error(p2, 2)

    one_qubit_gates = ["x", "h", "ry", "rz"]
    two_qubit_gates = ["cx"]

    for gate in one_qubit_gates:
        noise_model.add_all_qubit_quantum_error(error_1q, gate)

    for gate in two_qubit_gates:
        noise_model.add_all_qubit_quantum_error(error_2q, gate)

    return noise_model


def build_thermal_relaxation_noise_model(
    t1: float = 100e3,
    t2: float = 80e3,
    single_qubit_gate_time: float = 50.0,
    two_qubit_gate_time: float = 300.0,
) -> NoiseModel:
    """
    Build a simple thermal-relaxation noise model.

    Units:
    - t1, t2 in the same time units as gate times
    - defaults are illustrative for a toy simulation, not hardware-calibrated
    """
    if t1 <= 0 or t2 <= 0:
        raise ValueError("t1 and t2 must be positive")

    if single_qubit_gate_time <= 0 or two_qubit_gate_time <= 0:
        raise ValueError("gate times must be positive")

    noise_model = NoiseModel()

    error_1q = thermal_relaxation_error(t1, t2, single_qubit_gate_time)
    error_2q = thermal_relaxation_error(t1, t2, two_qubit_gate_time).tensor(
        thermal_relaxation_error(t1, t2, two_qubit_gate_time)
    )

    one_qubit_gates = ["x", "h", "ry", "rz"]
    two_qubit_gates = ["cx"]

    for gate in one_qubit_gates:
        noise_model.add_all_qubit_quantum_error(error_1q, gate)

    for gate in two_qubit_gates:
        noise_model.add_all_qubit_quantum_error(error_2q, gate)

    return noise_model


def noise_summary(noise_model: NoiseModel, model_name: str) -> dict:
    """
    Frontend-friendly summary of the chosen noise model.
    """
    return {
        "model_name": model_name,
        "basis_gates": list(noise_model.basis_gates),
        "description": (
            "Noise is added to the toy scrambling protocol to show how imperfect "
            "quantum evolution degrades information recovery."
        ),
    }