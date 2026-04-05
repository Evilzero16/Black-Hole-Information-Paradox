from __future__ import annotations

import os

from qiskit import ClassicalRegister, QuantumCircuit, transpile

from blackhole_paradox.metrics.fidelity import fidelity_summary
from blackhole_paradox.protocols.execution import (
    DecoderMode,
    _build_decoder_circuit,
    _extract_recovered_bits_from_counts,
    build_protocol_circuit,
)


def run_ibm_hardware_checkpoint(
    message: str,
    message_qubits: int = 4,
    black_hole_qubits: int = 3,
    reference_qubits: int = 2,
    scramble_depth: int = 3,
    decoder_mode: DecoderMode = "toy_argmax",
    shots: int = 512,
    backend_name: str | None = None,
    token_env_var: str = "IBM_QUANTUM_TOKEN",
) -> dict:
    """
    Run one small checkpoint circuit on IBM Quantum hardware.

    This function is intentionally minimal for free-tier usage:
    - shot count is modest
    - one decoder mode per run
    - one message checkpoint per job
    """
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        from qiskit_ibm_runtime import least_busy as runtime_least_busy
    except Exception as exc:  # pragma: no cover - dependency may be optional
        raise RuntimeError(
            "qiskit-ibm-runtime is required for hardware runs. "
            "Install it with `pip install qiskit-ibm-runtime`."
        ) from exc

    token = os.getenv(token_env_var)
    if not token:
        raise RuntimeError(
            f"Missing IBM token. Set environment variable `{token_env_var}` first."
        )

    base_circuit, registers, encoded_bits = build_protocol_circuit(
        message=message,
        message_qubits=message_qubits,
        black_hole_qubits=black_hole_qubits,
        reference_qubits=reference_qubits,
        scramble_depth=scramble_depth,
    )
    protocol_qc = _build_decoder_circuit(
        base_circuit=base_circuit,
        registers=registers,
        scramble_depth=scramble_depth,
        decoder_mode=decoder_mode,
    )

    measured = QuantumCircuit(protocol_qc.num_qubits, name="hp_hardware")
    measured.compose(protocol_qc, inplace=True)
    creg = ClassicalRegister(protocol_qc.num_qubits, "c")
    measured.add_register(creg)
    measured.measure(range(protocol_qc.num_qubits), range(protocol_qc.num_qubits))

    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    if backend_name:
        backend = service.backend(backend_name)
    else:
        candidates = service.backends(
            operational=True,
            simulator=False,
        )
        if len(candidates) == 0:
            raise RuntimeError("No operational IBM hardware backend available.")
        backend = runtime_least_busy(candidates)

    compiled = transpile(measured, backend=backend, optimization_level=1)
    job = backend.run(compiled, shots=shots)
    result = job.result()
    counts = result.get_counts()

    recovered_bits, top_projected = _extract_recovered_bits_from_counts(
        counts=counts,
        message_register=registers.message,
        total_qubits=protocol_qc.num_qubits,
    )

    return {
        "backend_name": backend.name,
        "job_id": job.job_id(),
        "decoder_mode": decoder_mode,
        "shots": shots,
        "message": message,
        "encoded_bits": encoded_bits,
        "recovered_bits": recovered_bits,
        "metrics": fidelity_summary(encoded_bits, recovered_bits),
        "top_projected_message_outcomes": top_projected,
        "note": (
            "Hardware checkpoints are noisy and stochastic. Compare trends with "
            "the noiseless and noisy-simulator references."
        ),
    }
