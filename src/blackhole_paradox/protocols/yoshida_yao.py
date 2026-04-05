from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from blackhole_paradox.circuits.scrambling import (
    build_black_hole_scrambler,
    build_inverse_scrambler,
    circuit_text_diagram,
    scrambler_metadata,
)
from blackhole_paradox.encoding import decode_register_bits_to_message, encoding_summary
from blackhole_paradox.metrics.entanglement import entanglement_summary
from blackhole_paradox.metrics.fidelity import fidelity_summary
from blackhole_paradox.protocols.entanglement import (
    circuit_text_diagram as entanglement_circuit_text_diagram,
    prepare_old_black_hole_entanglement,
)


@dataclass
class ProtocolRegisters:
    """
    Qubit layout for the toy Hayden-Preskill-style protocol.

    Total layout:
        [ R | B | M ]

    R = reference system entangled with the old black hole
    B = black hole register
    M = infalling message register
    """

    reference: list[int]
    black_hole: list[int]
    message: list[int]

    @property
    def all_qubits(self) -> list[int]:
        return self.reference + self.black_hole + self.message


DecoderMode = Literal["toy_argmax", "inverse_scrambler"]


def _prepare_message_basis_state(
    qc: QuantumCircuit,
    message_bits: str,
    message_qubits: list[int],
) -> None:
    """
    Prepare the message register in a computational basis state |message_bits>.
    """
    if len(message_bits) != len(message_qubits):
        raise ValueError("message_bits length must match number of message qubits")

    for bit, qubit in zip(message_bits, message_qubits):
        if bit == "1":
            qc.x(qubit)


def _extract_register_bits_from_statevector(
    statevector: Statevector,
    register_qubits: list[int],
    total_qubits: int,
) -> str:
    """
    Extract the most likely computational-basis bitstring on a chosen register.

    For the current toy demo, we decode by selecting the most likely global basis
    state and then reading off the chosen register bits.
    """
    probs = statevector.probabilities()
    max_index = int(np.argmax(probs))
    full_bits = format(max_index, f"0{total_qubits}b")
    return _extract_register_bits_from_full_bits(
        full_bits=full_bits,
        register_qubits=register_qubits,
        total_qubits=total_qubits,
    )


def _extract_register_bits_from_full_bits(
    full_bits: str,
    register_qubits: list[int],
    total_qubits: int,
) -> str:
    """
    Extract register bits from a full bitstring in Qiskit's label ordering.

    Qiskit prints/measures bitstrings as q_(n-1) ... q_0, so qubit q maps to
    index (n - 1 - q).
    """
    if len(full_bits) != total_qubits:
        raise ValueError("full_bits length must match total_qubits")
    return "".join(full_bits[total_qubits - 1 - q] for q in register_qubits)


def _decode_bits_to_text_safe(bits: str) -> dict:
    """
    Attempt UTF-8 decode for recovered bits while preserving failure reason.
    """
    if len(bits) % 8 != 0:
        return {
            "decoded_text": None,
            "decode_status": "not_byte_aligned",
            "decode_note": (
                "Recovered bits are not a multiple of 8, so UTF-8 text decoding "
                "is not directly possible."
            ),
        }

    try:
        decoded = decode_register_bits_to_message(bits)
    except Exception as exc:  # pragma: no cover - defensive path
        return {
            "decoded_text": None,
            "decode_status": "decode_error",
            "decode_note": f"UTF-8 decode failed: {exc}",
        }

    return {
        "decoded_text": decoded,
        "decode_status": "ok",
        "decode_note": "Recovered bits successfully decoded to UTF-8 text.",
    }


def _compose_old_black_hole_and_message(
    reference_qubits: int,
    black_hole_qubits: int,
    message_bits: str,
) -> tuple[QuantumCircuit, ProtocolRegisters]:
    """
    Build the initial circuit:
    1. Prepare old black hole entanglement between R and B
    2. Prepare message register M in a basis state

    Layout:
        [ R | B | M ]
    """
    if reference_qubits <= 0:
        raise ValueError("reference_qubits must be positive")
    if black_hole_qubits <= 0:
        raise ValueError("black_hole_qubits must be positive")
    if len(message_bits) == 0:
        raise ValueError("message_bits cannot be empty")

    message_qubits_count = len(message_bits)
    total_qubits = reference_qubits + black_hole_qubits + message_qubits_count

    qc = QuantumCircuit(total_qubits, name="HP_init")

    reference = list(range(reference_qubits))
    black_hole = list(range(reference_qubits, reference_qubits + black_hole_qubits))
    message = list(
        range(
            reference_qubits + black_hole_qubits,
            reference_qubits + black_hole_qubits + message_qubits_count,
        )
    )

    ent_qc, _ = prepare_old_black_hole_entanglement(
        reference_size=reference_qubits,
        black_hole_size=black_hole_qubits,
    )
    qc.compose(ent_qc, qubits=range(reference_qubits + black_hole_qubits), inplace=True)
    _prepare_message_basis_state(qc, message_bits=message_bits, message_qubits=message)

    registers = ProtocolRegisters(
        reference=reference,
        black_hole=black_hole,
        message=message,
    )
    return qc, registers


def run_yoshida_yao_protocol(
    message: str,
    message_qubits: int = 4,
    black_hole_qubits: int = 4,
    reference_qubits: int = 4,
    scramble_depth: int = 3,
    radiation_qubits: int = 2,
    decoder_modes: tuple[DecoderMode, ...] = ("toy_argmax", "inverse_scrambler"),
    seed: int | None = None,
) -> dict:
    """
    Run a version-1 Hayden-Preskill-style toy protocol.

    Conceptual steps:
    1. Encode a short classical message into a small message register M
    2. Prepare an old black hole B entangled with a reference system R
    3. Scramble the joint system (B + M)
    4. Designate some of the scrambled qubits as 'radiation'
    5. Attempt a toy recovery of the original message from the evolved state

    Important:
    - This is a pedagogical toy model, not a literal astrophysical simulation.
    - The current recovery step is a simplified readout from the post-scrambling state.
    """
    if not isinstance(message, str) or message == "":
        raise ValueError("message must be a non-empty string")

    if not isinstance(radiation_qubits, int) or radiation_qubits <= 0:
        raise ValueError("radiation_qubits must be a positive integer")
    if len(decoder_modes) == 0:
        raise ValueError("decoder_modes cannot be empty")

    encoding = encoding_summary(message, message_qubits)
    encoded_bits = encoding["padded_bits"]

    init_circuit, registers = _compose_old_black_hole_and_message(
        reference_qubits=reference_qubits,
        black_hole_qubits=black_hole_qubits,
        message_bits=encoded_bits,
    )

    total_qubits = (
        len(registers.reference) + len(registers.black_hole) + len(registers.message)
    )

    initial_state = Statevector.from_instruction(init_circuit)

    scrambling_register = registers.black_hole + registers.message
    scrambler = build_black_hole_scrambler(
        n_qubits=len(scrambling_register),
        depth=scramble_depth,
    )

    full_circuit = QuantumCircuit(total_qubits, name="HP_demo")
    full_circuit.compose(init_circuit, inplace=True)
    full_circuit.compose(scrambler, qubits=scrambling_register, inplace=True)

    final_state = Statevector.from_instruction(full_circuit)

    radiation_register = scrambling_register[: min(radiation_qubits, len(scrambling_register))]
    remaining_black_hole = scrambling_register[min(radiation_qubits, len(scrambling_register)) :]

    inverse_scrambler = build_inverse_scrambler(
        n_qubits=len(scrambling_register),
        depth=scramble_depth,
    )
    inverse_full_circuit = QuantumCircuit(total_qubits, name="HP_inverse_decode")
    inverse_full_circuit.compose(full_circuit, inplace=True)
    inverse_full_circuit.compose(
        inverse_scrambler,
        qubits=scrambling_register,
        inplace=True,
    )
    inverse_decoded_state = Statevector.from_instruction(inverse_full_circuit)

    decoder_results: dict[str, dict] = {}
    for mode in decoder_modes:
        if mode == "toy_argmax":
            recovered_bits = _extract_register_bits_from_statevector(
                statevector=final_state,
                register_qubits=registers.message,
                total_qubits=total_qubits,
            )
            decoder_description = (
                "Selects the most likely basis outcome after scrambling and reads "
                "message-register bits. Pedagogical, not a scalable decoder."
            )
        elif mode == "inverse_scrambler":
            recovered_bits = _extract_register_bits_from_statevector(
                statevector=inverse_decoded_state,
                register_qubits=registers.message,
                total_qubits=total_qubits,
            )
            decoder_description = (
                "Applies the exact inverse scrambling unitary as an idealized "
                "best-case reference with full unitary knowledge."
            )
        else:
            raise ValueError(f"Unsupported decoder mode: {mode}")

        text_result = _decode_bits_to_text_safe(recovered_bits)
        decoder_results[mode] = {
            "decoder_mode": mode,
            "description": decoder_description,
            "original_encoded_bits": encoded_bits,
            "recovered_bits": recovered_bits,
            "metrics": fidelity_summary(encoded_bits, recovered_bits),
            **text_result,
        }

    primary_decoder = decoder_modes[0]
    primary_result = decoder_results[primary_decoder]
    metrics = primary_result["metrics"]

    stages: list[dict] = []

    stages.append(
        {
            "stage": "input",
            "title": "User Input",
            "description": "A short message is provided as the information thrown into the toy black hole.",
            "data": {
                "message": message,
                "message_length": len(message),
            },
        }
    )

    stages.append(
        {
            "stage": "encoding",
            "title": "Message Encoding",
            "description": (
                "The message is converted to UTF-8 bits and compressed into a small "
                "computational-basis register that represents the infalling information."
            ),
            "data": encoding,
        }
    )

    ent_qc, ent_resource = prepare_old_black_hole_entanglement(
        reference_size=reference_qubits,
        black_hole_size=black_hole_qubits,
    )
    stages.append(
        {
            "stage": "black_hole_setup",
            "title": "Old Black Hole Setup",
            "description": (
                "The black hole is prepared already entangled with an external "
                "reference system, mimicking the Hayden-Preskill idea of an old black hole."
            ),
            "data": {
                "reference_qubits": ent_resource.reference_qubits,
                "black_hole_qubits": ent_resource.black_hole_qubits,
                "num_entangled_pairs": ent_resource.num_pairs,
                "circuit_diagram": entanglement_circuit_text_diagram(ent_qc),
                "register_layout": {
                    "reference": registers.reference,
                    "black_hole": registers.black_hole,
                    "message": registers.message,
                },
            },
        }
    )

    scr_meta = scrambler_metadata(scrambler, depth=scramble_depth)
    stages.append(
        {
            "stage": "scrambling",
            "title": "Scrambling",
            "description": (
                "A toy scrambling unitary acts on the combined black-hole and infalling "
                "message registers, spreading initially localized information across the system."
            ),
            "data": {
                "scrambling_qubits": scrambling_register,
                "depth": scr_meta.depth,
                "gate_count": scr_meta.gate_count,
                "operation_counts": scr_meta.operation_counts,
                "circuit_diagram": circuit_text_diagram(scrambler),
            },
        }
    )

    initial_scrambling_subsystem = entanglement_summary(
        statevector=initial_state.data,
        subsystem_qubits=scrambling_register,
        num_qubits=total_qubits,
    )
    final_scrambling_subsystem = entanglement_summary(
        statevector=final_state.data,
        subsystem_qubits=scrambling_register,
        num_qubits=total_qubits,
    )

    stages.append(
        {
            "stage": "entanglement_growth",
            "title": "Entanglement Growth",
            "description": (
                "As scrambling proceeds, the information becomes more delocalized and "
                "the subsystem becomes more entangled with the rest of the total state."
            ),
            "data": {
                "before_scrambling": initial_scrambling_subsystem,
                "after_scrambling": final_scrambling_subsystem,
            },
        }
    )

    stages.append(
        {
            "stage": "radiation_split",
            "title": "Radiation Partition",
            "description": (
                "Part of the scrambled system is interpreted as emitted Hawking radiation, "
                "while the rest remains in the black hole."
            ),
            "data": {
                "radiation_qubits": radiation_register,
                "remaining_black_hole_qubits": remaining_black_hole,
                "note": (
                    "In this toy model, the radiation subsystem is defined by selecting "
                    "a subset of the scrambled qubits."
                ),
            },
        }
    )

    stages.append(
        {
            "stage": "decoding",
            "title": "Decoder Comparison",
            "description": (
                "Multiple decoder views are shown: a pedagogical argmax readout and "
                "an idealized inverse-scrambler baseline."
            ),
            "data": {
                "available_decoders": list(decoder_modes),
                "primary_decoder_mode": primary_decoder,
                "decoder_results": decoder_results,
            },
        }
    )

    stages.append(
        {
            "stage": "comparison",
            "title": "Recovery Comparison",
            "description": (
                "The recovered message block is compared against the original encoded block."
            ),
            "data": metrics,
        }
    )

    return {
        "config": {
            "message": message,
            "message_qubits": message_qubits,
            "black_hole_qubits": black_hole_qubits,
            "reference_qubits": reference_qubits,
            "radiation_qubits": radiation_qubits,
            "scramble_depth": scramble_depth,
            "decoder_modes": list(decoder_modes),
            "seed": seed,
        },
        "input_message": message,
        "input_bits": encoding["utf8_bits"],
        "encoded_block": encoded_bits,
        "decoder_results": decoder_results,
        "primary_decoder_mode": primary_decoder,
        "recovered_bits": primary_result["recovered_bits"],
        "recovered_message": (
            primary_result["decoded_text"]
            if primary_result["decoded_text"] is not None
            else primary_result["recovered_bits"]
        ),
        "metrics": metrics,
        "stages": stages,
        "notes": [
            (
                "This is a toy quantum-information demo inspired by Hayden-Preskill and "
                "related black-hole information protocols."
            ),
            (
                "The message is encoded into a small basis-state register, so the recovered "
                "output may be shown as bits unless the register width is byte-aligned."
            ),
        ],
    }