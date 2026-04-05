# Black Hole Information Paradox (Interactive Toy Simulator)

This repository provides an educational, interactive simulation of black-hole
information scrambling and recovery using small quantum circuits.

Users can input a classical message, observe each protocol stage, and compare
decoder behavior under ideal and noisy conditions.

## What This Project Simulates

The core flow is a toy Hayden-Preskill-style protocol:

1. Encode user text into a small message register.
2. Prepare an old black-hole resource entangled with a reference system.
3. Scramble the combined black-hole and message subsystem.
4. Partition part of that subsystem as "radiation".
5. Attempt recovery with multiple decoder views.
6. Compare recovery quality with fidelity-oriented metrics.

## Scientific Scope (Important)

This is a quantum information toy model, not a literal astrophysical
black-hole simulation.

- Small qubit counts are used intentionally for free-tier accessibility.
- Decoder modes include pedagogical approximations:
  - `toy_argmax`: most-likely basis readout after scrambling.
  - `inverse_scrambler`: idealized baseline that assumes full unitary knowledge.
- Results show trends in information flow and recovery behavior, not
  experimental claims about real black holes.

## Interactive Demo (Local Streamlit)

From repository root:

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

The app exposes:

- user message input
- qubit/depth controls
- decoder comparison
- stage-by-stage protocol trace
- optional noisy simulator sweeps
- optional IBM hardware checkpoint execution

## Optional IBM Hardware Checkpoint

Install dependencies and set your token:

```bash
pip install qiskit-ibm-runtime
export IBM_QUANTUM_TOKEN="your_token_here"
```

Then enable the hardware checkpoint toggle inside the Streamlit app.

Notes:

- Keep runs small (few qubits, modest depth, limited shots) to stay within
  free-tier runtime constraints.
- Hardware mode is opt-in; simulator mode is default.

## CLI Usage

You can also run from CLI:

```bash
python -m blackhole_paradox.run --message "hello" --mode protocol
```

Noise sweep example:

```bash
python -m blackhole_paradox.run --message "hello" --mode noise --p2-values "0.0,0.01,0.02"
```

Hardware checkpoint example:

```bash
python -m blackhole_paradox.run --message "hello" --mode hardware --shots 512
```

## Repository Highlights

- Core protocol: `src/blackhole_paradox/protocols/yoshida_yao.py`
- Noise execution helpers: `src/blackhole_paradox/protocols/execution.py`
- IBM checkpoint helper: `src/blackhole_paradox/hardware/ibm_runtime.py`
- Streamlit app: `app/streamlit_app.py`
- Tests: `tests/`

## Research References Used for Design Direction

- Yoshida and Kitaev, efficient decoding for Hayden-Preskill:
  [arXiv:1710.03363](https://arxiv.org/abs/1710.03363)
- Rampp and Claeys, Hayden-Preskill recovery in chaotic/integrable circuits:
  [Quantum 2024](https://quantum-journal.org/papers/q-2024-08-08-1434/)
- IBM Quantum plan details (runtime and access can change over time):
  [IBM Plans Overview](https://quantum.cloud.ibm.com/docs/guides/plans-overview)
