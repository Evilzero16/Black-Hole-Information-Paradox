from blackhole_paradox.protocols.execution import run_depolarizing_noise_sweep
from blackhole_paradox.protocols.yoshida_yao import run_yoshida_yao_protocol


def test_protocol_stage_schema_and_decoders() -> None:
    result = run_yoshida_yao_protocol(
        message="A",
        message_qubits=4,
        black_hole_qubits=3,
        reference_qubits=2,
        scramble_depth=2,
        radiation_qubits=2,
        decoder_modes=("toy_argmax", "inverse_scrambler"),
    )

    assert "stages" in result
    assert isinstance(result["stages"], list)
    assert len(result["stages"]) >= 7
    assert "decoder_results" in result
    assert set(result["decoder_results"].keys()) == {
        "toy_argmax",
        "inverse_scrambler",
    }

    for mode, payload in result["decoder_results"].items():
        assert payload["decoder_mode"] == mode
        assert "recovered_bits" in payload
        assert "metrics" in payload
        assert set(payload["metrics"].keys()) == {
            "fidelity",
            "success_probability",
            "bitwise_accuracy",
        }


def test_inverse_scrambler_recovers_encoded_bits_in_ideal_case() -> None:
    result = run_yoshida_yao_protocol(
        message="A",
        message_qubits=4,
        black_hole_qubits=3,
        reference_qubits=2,
        scramble_depth=3,
        radiation_qubits=2,
        decoder_modes=("inverse_scrambler",),
    )

    decoded = result["decoder_results"]["inverse_scrambler"]["recovered_bits"]
    assert decoded == result["encoded_block"]
    assert result["metrics"]["fidelity"] == 1.0


def test_noise_sweep_returns_trial_series() -> None:
    sweep = run_depolarizing_noise_sweep(
        message="A",
        message_qubits=4,
        black_hole_qubits=3,
        reference_qubits=2,
        scramble_depth=2,
        decoder_mode="toy_argmax",
        p2_values=[0.0, 0.02],
        p1_ratio=0.1,
        shots=512,
    )

    assert sweep["decoder_mode"] == "toy_argmax"
    assert len(sweep["trials"]) == 2
    for trial in sweep["trials"]:
        assert "metrics" in trial
        assert "recovered_bits" in trial
