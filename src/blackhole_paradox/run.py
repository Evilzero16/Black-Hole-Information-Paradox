from __future__ import annotations

import argparse
import json

from blackhole_paradox.hardware.ibm_runtime import run_ibm_hardware_checkpoint
from blackhole_paradox.protocols.execution import run_depolarizing_noise_sweep
from blackhole_paradox.protocols.yoshida_yao import run_yoshida_yao_protocol


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the black-hole information toy simulation."
    )
    parser.add_argument("--message", required=True, help="Input message")
    parser.add_argument("--message-qubits", type=int, default=4)
    parser.add_argument("--black-hole-qubits", type=int, default=3)
    parser.add_argument("--reference-qubits", type=int, default=2)
    parser.add_argument("--scramble-depth", type=int, default=3)
    parser.add_argument("--radiation-qubits", type=int, default=2)
    parser.add_argument(
        "--decoder-modes",
        default="toy_argmax,inverse_scrambler",
        help="Comma-separated decoder modes",
    )
    parser.add_argument(
        "--mode",
        choices=["protocol", "noise", "hardware"],
        default="protocol",
        help="Execution mode",
    )
    parser.add_argument("--p2-values", default="0.0,0.005,0.01,0.02")
    parser.add_argument("--p1-ratio", type=float, default=0.1)
    parser.add_argument("--shots", type=int, default=2048)
    parser.add_argument("--backend-name", default="")
    parser.add_argument("--token-env-var", default="IBM_QUANTUM_TOKEN")
    args = parser.parse_args()

    decoder_modes = tuple(
        mode.strip() for mode in args.decoder_modes.split(",") if mode.strip()
    )

    if args.mode == "protocol":
        result = run_yoshida_yao_protocol(
            message=args.message,
            message_qubits=args.message_qubits,
            black_hole_qubits=args.black_hole_qubits,
            reference_qubits=args.reference_qubits,
            scramble_depth=args.scramble_depth,
            radiation_qubits=args.radiation_qubits,
            decoder_modes=decoder_modes,  # type: ignore[arg-type]
        )
    elif args.mode == "noise":
        p2_values = [float(piece.strip()) for piece in args.p2_values.split(",")]
        result = run_depolarizing_noise_sweep(
            message=args.message,
            message_qubits=args.message_qubits,
            black_hole_qubits=args.black_hole_qubits,
            reference_qubits=args.reference_qubits,
            scramble_depth=args.scramble_depth,
            decoder_mode=decoder_modes[0],  # type: ignore[arg-type]
            p2_values=p2_values,
            p1_ratio=args.p1_ratio,
            shots=args.shots,
        )
    else:
        result = run_ibm_hardware_checkpoint(
            message=args.message,
            message_qubits=args.message_qubits,
            black_hole_qubits=args.black_hole_qubits,
            reference_qubits=args.reference_qubits,
            scramble_depth=args.scramble_depth,
            decoder_mode=decoder_modes[0],  # type: ignore[arg-type]
            shots=args.shots,
            backend_name=args.backend_name or None,
            token_env_var=args.token_env_var,
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
