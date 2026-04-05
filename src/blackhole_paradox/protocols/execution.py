from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

from qiskit import ClassicalRegister, QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from blackhole_paradox.circuits.scrambling import (
    build_black_hole_scrambler,
    build_inverse_scrambler,
)
from blackhole_paradox.encoding import decode_register_bits_to_message, encoding_summary
from blackhole_paradox.metrics.fidelity import fidelity_summary
from blackhole_paradox.noise.aer_models import build_depolarizing_noise_model
from blackhole_paradox.protocols.entanglement import prepare_old_black_hole_entanglement

DecoderMode = Literal["toy_argmax", "inverse_scrambler"]


@dataclass
class ExecutionRegisters:
    reference: list[int]
    black_hole: list[int]
    message: list[int]

    @property
    def scrambling(self) -> list[int]:
        return self.black_hole + self.message


def _extract_register_bits_from_full_bits(
    full_bits: str,
    register_qubits: list[int],
    total_qubits: int,
) -> str:
    return "".join(full_bits[total_qubits - 1 - q] for q in register_qubits)


def _decode_bits_to_text_safe(bits: str) -> str | None:
    if len(bits) % 8 != 0:
        return None
    try:
        return decode_register_bits_to_message(bits)
    except Exception:
        return None


def build_protocol_circuit(
    message: str,
    message_qubits: int,
    black_hole_qubits: int,
    reference_qubits: int,
    scramble_depth: int,
) -> tuple[QuantumCircuit, ExecutionRegisters, str]:
    encoding = encoding_summary(message, message_qubits)
    encoded_bits = encoding["padded_bits"]

    total_qubits = message_qubits + black_hole_qubits + reference_qubits
    qc = QuantumCircuit(total_qubits, name="HP_exec")

    reference = list(range(reference_qubits))
    black_hole = list(range(reference_qubits, reference_qubits + black_hole_qubits))
    message_register = list(
        range(
            reference_qubits + black_hole_qubits,
            reference_qubits + black_hole_qubits + message_qubits,
        )
    )

    ent_qc, _ = prepare_old_black_hole_entanglement(
        reference_size=reference_qubits,
        black_hole_size=black_hole_qubits,
    )
    qc.compose(ent_qc, qubits=range(reference_qubits + black_hole_qubits), inplace=True)

    for bit, qubit in zip(encoded_bits, message_register):
        if bit == "1":
            qc.x(qubit)

    scrambler = build_black_hole_scrambler(
        n_qubits=black_hole_qubits + message_qubits,
        depth=scramble_depth,
    )
    qc.compose(scrambler, qubits=black_hole + message_register, inplace=True)

    return qc, ExecutionRegisters(reference, black_hole, message_register), encoded_bits


def _build_decoder_circuit(
    base_circuit: QuantumCircuit,
    registers: ExecutionRegisters,
    scramble_depth: int,
    decoder_mode: DecoderMode,
) -> QuantumCircuit:
    qc = QuantumCircuit(base_circuit.num_qubits, name=f"{decoder_mode}_run")
    qc.compose(base_circuit, inplace=True)

    if decoder_mode == "inverse_scrambler":
        inverse = build_inverse_scrambler(
            n_qubits=len(registers.scrambling),
            depth=scramble_depth,
        )
        qc.compose(inverse, qubits=registers.scrambling, inplace=True)
    elif decoder_mode != "toy_argmax":
        raise ValueError(f"Unsupported decoder mode: {decoder_mode}")

    return qc


def _extract_recovered_bits_from_counts(
    counts: dict[str, int],
    message_register: list[int],
    total_qubits: int,
) -> tuple[str, list[dict]]:
    # Choose most likely global outcome, then project onto message register.
    most_common_full_bits, _ = max(counts.items(), key=lambda kv: kv[1])
    recovered_bits = _extract_register_bits_from_full_bits(
        full_bits=most_common_full_bits,
        register_qubits=message_register,
        total_qubits=total_qubits,
    )

    # Also provide top few projected message outcomes for UI inspection.
    projected = Counter()
    for full_bits, count in counts.items():
        projected_bits = _extract_register_bits_from_full_bits(
            full_bits=full_bits,
            register_qubits=message_register,
            total_qubits=total_qubits,
        )
        projected[projected_bits] += count

    total = sum(projected.values())
    top_projected = []
    for bits, count in projected.most_common(5):
        top_projected.append(
            {
                "bits": bits,
                "counts": count,
                "probability": count / total if total > 0 else 0.0,
            }
        )

    return recovered_bits, top_projected


def run_noisy_decoder_trial(
    message: str,
    message_qubits: int = 4,
    black_hole_qubits: int = 3,
    reference_qubits: int = 2,
    scramble_depth: int = 3,
    decoder_mode: DecoderMode = "toy_argmax",
    p1: float = 0.001,
    p2: float = 0.01,
    shots: int = 2048,
) -> dict:
    """
    Execute one noisy-shot trial and decode message-register bits.
    """
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

    measured = QuantumCircuit(protocol_qc.num_qubits, name="measured")
    measured.compose(protocol_qc, inplace=True)
    creg = ClassicalRegister(protocol_qc.num_qubits, "c")
    measured.add_register(creg)
    measured.measure(range(protocol_qc.num_qubits), range(protocol_qc.num_qubits))

    noise_model = build_depolarizing_noise_model(p1=p1, p2=p2)
    simulator = AerSimulator(noise_model=noise_model)
    compiled = transpile(measured, simulator)
    result = simulator.run(compiled, shots=shots).result()
    counts = result.get_counts()

    recovered_bits, top_projected = _extract_recovered_bits_from_counts(
        counts=counts,
        message_register=registers.message,
        total_qubits=protocol_qc.num_qubits,
    )

    return {
        "decoder_mode": decoder_mode,
        "noise": {"model": "depolarizing", "p1": p1, "p2": p2},
        "shots": shots,
        "encoded_bits": encoded_bits,
        "recovered_bits": recovered_bits,
        "decoded_text": _decode_bits_to_text_safe(recovered_bits),
        "metrics": fidelity_summary(encoded_bits, recovered_bits),
        "top_projected_message_outcomes": top_projected,
    }


def run_depolarizing_noise_sweep(
    message: str,
    message_qubits: int = 4,
    black_hole_qubits: int = 3,
    reference_qubits: int = 2,
    scramble_depth: int = 3,
    decoder_mode: DecoderMode = "toy_argmax",
    p2_values: list[float] | None = None,
    p1_ratio: float = 0.1,
    shots: int = 2048,
) -> dict:
    """
    Sweep two-qubit depolarizing probability and report recovery metrics.
    """
    if p2_values is None:
        p2_values = [0.0, 0.005, 0.01, 0.02, 0.04]
    if p1_ratio < 0.0:
        raise ValueError("p1_ratio must be non-negative")

    trials = []
    for p2 in p2_values:
        trial = run_noisy_decoder_trial(
            message=message,
            message_qubits=message_qubits,
            black_hole_qubits=black_hole_qubits,
            reference_qubits=reference_qubits,
            scramble_depth=scramble_depth,
            decoder_mode=decoder_mode,
            p1=p1_ratio * p2,
            p2=p2,
            shots=shots,
        )
        trials.append(trial)

    return {
        "decoder_mode": decoder_mode,
        "message": message,
        "p2_values": p2_values,
        "p1_ratio": p1_ratio,
        "trials": trials,
        "note": (
            "Two-qubit gate noise is the dominant knob in this toy sweep, while "
            "single-qubit noise is set proportionally by p1_ratio."
        ),
    }
