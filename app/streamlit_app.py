from __future__ import annotations

import html
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from blackhole_paradox.encoding import encoding_summary
from blackhole_paradox.hardware.ibm_runtime import run_ibm_hardware_checkpoint
from blackhole_paradox.protocols.execution import run_depolarizing_noise_sweep
from blackhole_paradox.protocols.yoshida_yao import run_yoshida_yao_protocol


def _parse_float_list(raw: str) -> list[float]:
    values = []
    for chunk in raw.split(","):
        text = chunk.strip()
        if text == "":
            continue
        values.append(float(text))
    return values


def _recovery_story_badge(fidelity: float, bitwise_accuracy: float) -> tuple[str, str]:
    """Return (short_label, emoji) for non-expert viewers."""
    if fidelity >= 0.999:
        return "Full match", "✅"
    if bitwise_accuracy >= 0.75:
        return "Mostly recovered", "🟡"
    if bitwise_accuracy >= 0.45:
        return "Partially recovered", "🟠"
    return "Poor match", "🔴"


def _decoder_plain_name(mode: str) -> str:
    return {
        "toy_argmax": "Quick readout (pedagogical)",
        "inverse_scrambler": "Ideal unscramble (best-case reference)",
    }.get(mode, mode)


def _render_pipeline_html() -> None:
    """Simple visual flow: one screen-friendly story, no jargon."""
    steps = [
        ("1", "Your text", "What you type"),
        ("2", "Bits", "Message as 0/1"),
        ("3", "Old BH + ref", "Entangled setup"),
        ("4", "Scramble", "Info spreads"),
        ("5", "Radiation split", "Part “escapes”"),
        ("6", "Decode", "Try to read back"),
        ("7", "Compare", "Did we match?"),
    ]
    parts = []
    for num, title, sub in steps:
        parts.append(
            f'<div style="flex:1 1 120px; min-width:100px; border:1px solid #3d3d3d; '
            f"border-radius:10px; padding:10px 8px; text-align:center; "
            f'background:#161616;">'
            f'<div style="font-size:0.75rem;opacity:0.7;">Step {num}</div>'
            f'<div style="font-weight:600;margin:4px 0;">{html.escape(title)}</div>'
            f'<div style="font-size:0.8rem;opacity:0.85;">{html.escape(sub)}</div>'
            f"</div>"
        )
    inner = '<span style="color:#888;padding:0 4px;">→</span>'.join(parts)
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;align-items:stretch;justify-content:center;'
        f'gap:6px;margin:12px 0 8px 0;">{inner}</div>',
        unsafe_allow_html=True,
    )


def _render_utf8_bits_highlighted(utf8_bits: str, message_qubits: int) -> None:
    """Show full UTF-8 bitstream with the first M bits highlighted (what the toy register holds)."""
    spans = []
    for i, ch in enumerate(utf8_bits):
        is_used = i < message_qubits
        bg = "#1e4d33" if is_used else "#2d2d2d"
        border = "#3ecf8e" if is_used else "transparent"
        spans.append(
            f'<span style="background:{bg};border-bottom:2px solid {border};'
            f'padding:2px 1px;margin:0;font-family:ui-monospace,monospace;font-size:0.78rem;">'
            f"{html.escape(ch)}</span>"
        )
    bits_html = "".join(spans)
    st.markdown(
        "<div style='opacity:0.85;font-size:0.85rem;margin-bottom:6px;'>"
        "<strong>UTF-8 bits</strong> "
        "<span style='opacity:0.8'>(green underline = the first <code>M</code> bits that go into the "
        "message register; the rest is ignored in this toy model)</span></div>"
        "<div style='line-height:1.85;word-break:break-all;max-height:140px;overflow:auto;padding:8px;"
        "border:1px solid #3d3d3d;border-radius:8px;background:#121212;'>"
        + bits_html
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_start_and_end_cards(
    *,
    original_text: str,
    encoded_block: str,
    recovered_bits: str,
    decoded_text: str | None,
    message_qubits: int,
) -> None:
    """Large visual: start (text + M-bit pattern) vs end (recovered text + bits)."""
    orig_display = html.escape(original_text) if original_text else "(empty)"
    enc_block_esc = html.escape(encoded_block)
    rec_bits_esc = html.escape(recovered_bits)
    if decoded_text is not None:
        end_text_esc = html.escape(decoded_text)
        end_text_note = "Decoded from recovered bits (valid UTF-8 at this length)."
    else:
        end_text_esc = "—"
        end_text_note = (
            f"No UTF-8 text shown: recovered length is {message_qubits} bits "
            "(not a multiple of 8, or bytes are invalid)."
        )

    end_note = (
        f"The toy message register has <strong>{message_qubits}</strong> bit(s). "
        "Compare <strong>Start bits</strong> vs <strong>End bits</strong> to see the recovery."
    )

    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;align-items:stretch;justify-content:center;gap:16px;margin:16px 0;">'
        f'<div style="flex:1 1 280px;max-width:520px;border:2px solid #2d6a4f;border-radius:14px;padding:18px 16px;background:linear-gradient(165deg,#14261c,#0f1720);">'
        f'<div style="font-size:0.75rem;opacity:0.75;text-transform:uppercase;letter-spacing:0.06em;">Start</div>'
        f'<div style="margin-top:10px;font-size:0.78rem;opacity:0.85;text-transform:uppercase;">Original text</div>'
        f'<div style="font-size:clamp(1.25rem, 2.8vw, 1.85rem);font-weight:600;margin-top:6px;line-height:1.25;word-break:break-word;font-family:system-ui,sans-serif;">{orig_display}</div>'
        f'<div style="margin-top:16px;font-size:0.78rem;opacity:0.85;text-transform:uppercase;">Original bits (M-bit block in the register)</div>'
        f'<div style="margin-top:6px;font-size:1.05rem;font-family:ui-monospace,monospace;letter-spacing:0.06em;word-break:break-all;">{enc_block_esc}</div>'
        f'<div style="margin-top:10px;font-size:0.82rem;opacity:0.75;">This is the classical info loaded into the message qubits before scrambling.</div>'
        f"</div>"
        f'<div style="display:flex;align-items:center;font-size:1.8rem;color:#888;padding:8px 0;">→</div>'
        f'<div style="flex:1 1 280px;max-width:520px;border:2px solid #3a5a9a;border-radius:14px;padding:18px 16px;background:linear-gradient(165deg,#151a2e,#0f1720);">'
        f'<div style="font-size:0.75rem;opacity:0.75;text-transform:uppercase;letter-spacing:0.06em;">End</div>'
        f'<div style="margin-top:10px;font-size:0.78rem;opacity:0.85;text-transform:uppercase;">Recovered text</div>'
        f'<div style="font-size:clamp(1.15rem, 2.6vw, 1.65rem);font-weight:600;margin-top:6px;line-height:1.3;word-break:break-word;font-family:system-ui,sans-serif;">{end_text_esc}</div>'
        f'<div style="margin-top:8px;font-size:0.8rem;opacity:0.8;">{html.escape(end_text_note)}</div>'
        f'<div style="margin-top:16px;font-size:0.78rem;opacity:0.85;text-transform:uppercase;">Recovered bits</div>'
        f'<div style="margin-top:6px;font-size:1.05rem;font-family:ui-monospace,monospace;letter-spacing:0.06em;word-break:break-all;">{rec_bits_esc}</div>'
        f'<div style="margin-top:12px;font-size:0.82rem;opacity:0.85;">{end_note}</div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _explain_qubits_vs_letters(enc: dict) -> None:
    """Clarify M = number of bits in the register, not letters."""
    n_chars = len(enc["original_message"])
    n_utf8_bits = len(enc["utf8_bits"])
    m = enc["message_qubits"]
    st.markdown(
        f"""
**Why your word can be long but we only use a few qubits**

- **Letters ≠ qubits.** Your text is converted to **UTF-8 bits** (often **8 bits per ASCII letter**, more for emoji/Unicode).
- **Message qubits = M** means the quantum register stores exactly **M binary digits (0/1)** — the first **M** bits of that UTF-8 stream (padded with zeros if needed).
- So a **4-letter** word might need **32 bits** in UTF-8, but if **M = 4**, we only keep the **first 4 bits** of that stream. The simulator is **not** storing “4 letters”; it is storing a **tiny prefix** of the bit representation.

**This run:** {n_chars} character(s) → **{n_utf8_bits}** UTF-8 bits total → toy register uses **{m}** bit(s) = `{enc["padded_bits"]}`.
        """
    )


def _render_encoding_preview(enc: dict) -> None:
    """Before/after run: show how text maps to the M-bit block."""
    _explain_qubits_vs_letters(enc)
    _render_utf8_bits_highlighted(enc["utf8_bits"], enc["message_qubits"])
    st.markdown(
        f"**The {enc['message_qubits']}-bit block loaded into the message register (computational basis):** "
        f"`{enc['padded_bits']}`  \n"
        f"*Basis label:* `{enc.get('basis_label', '|' + enc['padded_bits'] + '>')}`"
    )


def _render_bit_compare(encoded: str, recovered: str) -> None:
    """Show bits with per-position highlight (match vs mismatch)."""
    n = max(len(encoded), len(recovered))
    enc_spans = []
    rec_spans = []
    for i in range(n):
        e = encoded[i] if i < len(encoded) else "·"
        r = recovered[i] if i < len(recovered) else "·"
        match = e == r and e in "01"
        bg_e = "#1a3d2e" if match else "#2a2a2a"
        bg_r = "#1a3d2e" if match else "#4a2a2a"
        enc_spans.append(
            f'<span style="background:{bg_e};padding:2px 4px;margin:1px;border-radius:4px;'
            f'font-family:ui-monospace,monospace;">{html.escape(e)}</span>'
        )
        rec_spans.append(
            f'<span style="background:{bg_r};padding:2px 4px;margin:1px;border-radius:4px;'
            f'font-family:ui-monospace,monospace;">{html.escape(r)}</span>'
        )
    st.markdown(
        "<div style='font-size:0.9rem;margin-bottom:6px;'><strong>Encoded block</strong> "
        "<span style='opacity:0.75'>(green = same bit as recovery below)</span></div>"
        f"<div style='line-height:1.9;'>{''.join(enc_spans)}</div>"
        "<div style='font-size:0.9rem;margin:10px 0 6px 0;'><strong>Recovered block</strong> "
        "<span style='opacity:0.75'>(green = match, red = mismatch)</span></div>"
        f"<div style='line-height:1.9;'>{''.join(rec_spans)}</div>",
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Black-Hole Message Recovery Demo", layout="wide")
st.title("Interactive Black-Hole Message Recovery")
st.caption(
    "Toy Hayden-Preskill-inspired simulation. Educational demo of information "
    "flow in small quantum circuits, not a literal astrophysical model."
)

with st.expander("Start here — what is this? (30 seconds)", expanded=True):
    st.markdown(
        """
**In one sentence:** we pretend your message is a tiny pattern of quantum bits, mix it up like a “black hole”
would scramble information, then try to read the pattern back and score how well we did.

**Why two decoders?**
- **Quick readout** is like guessing the most likely outcome after mixing — often imperfect, easy to explain.
- **Ideal unscramble** is the “cheating” best case: we exactly reverse the mixing. Use it to see what *perfect*
  recovery looks like in this toy model.

This is **not** a real astrophysical simulation — it is a small quantum information story you can watch step by step.
        """
    )
    _render_pipeline_html()

with st.sidebar:
    st.header("Protocol Controls")
    message = st.text_input("Input message", value="hello")
    message_qubits = st.slider(
        "Message qubits (M)",
        min_value=2,
        max_value=8,
        value=4,
        help="Not ‘letters’ — this is how many binary digits (0/1) the message register holds: "
        "the first M bits of your UTF-8 bitstream.",
    )
    black_hole_qubits = st.slider(
        "Black-hole qubits (B)", min_value=2, max_value=8, value=3
    )
    reference_qubits = st.slider(
        "Reference qubits (R)", min_value=1, max_value=6, value=2
    )
    scramble_depth = st.slider("Scrambler depth", min_value=1, max_value=8, value=3)
    radiation_qubits = st.slider("Radiation qubits", min_value=1, max_value=6, value=2)
    decoder_modes = st.multiselect(
        "Decoders to run",
        options=["toy_argmax", "inverse_scrambler"],
        default=["toy_argmax", "inverse_scrambler"],
    )

    st.divider()
    st.header("Noise Sweep (Simulator)")
    run_noise = st.checkbox("Run depolarizing noise sweep", value=True)
    p2_values_raw = st.text_input("Two-qubit p2 values", value="0.0, 0.005, 0.01, 0.02")
    p1_ratio = st.number_input("Single-qubit ratio p1 = p1_ratio * p2", 0.0, 1.0, 0.1, 0.01)
    noise_shots = st.number_input("Noise sweep shots", 256, 8192, 2048, 256)

    st.divider()
    st.header("IBM Hardware Checkpoint")
    run_hardware = st.checkbox("Run optional IBM hardware checkpoint", value=False)
    backend_name = st.text_input("Backend name (optional)", value="")
    hardware_decoder = st.selectbox(
        "Hardware decoder",
        options=["toy_argmax", "inverse_scrambler"],
        index=0,
    )
    hardware_shots = st.number_input("Hardware shots", 128, 4096, 512, 128)
    token_env_var = st.text_input("IBM token env var", value="IBM_QUANTUM_TOKEN")

    st.divider()
    st.header("Display")
    show_expert_json = st.checkbox("Show raw JSON in stages", value=False)

    run_clicked = st.button("Run Demo", type="primary", use_container_width=True)

if not run_clicked:
    st.info("Adjust the sidebar, then click **Run Demo** to simulate scrambling and recovery.")
    enc_preview = encoding_summary(message, message_qubits)
    st.subheader("Preview: text → bits (no simulation yet)")
    _render_encoding_preview(enc_preview)
    st.caption(
        "Tip: increase **Message qubits (M)** to keep more of your UTF-8 bitstream "
        "(M = 8 often fits one ASCII character; M = 4 is only half a byte)."
    )
    st.stop()

if not decoder_modes:
    st.error("Select at least one decoder mode.")
    st.stop()

protocol = run_yoshida_yao_protocol(
    message=message,
    message_qubits=message_qubits,
    black_hole_qubits=black_hole_qubits,
    reference_qubits=reference_qubits,
    scramble_depth=scramble_depth,
    radiation_qubits=radiation_qubits,
    decoder_modes=tuple(decoder_modes),
)

enc = encoding_summary(message, message_qubits)
primary_mode = protocol["primary_decoder_mode"]
primary_result = protocol["decoder_results"][primary_mode]

st.subheader("Visual: start → end")
_render_start_and_end_cards(
    original_text=protocol["input_message"],
    encoded_block=protocol["encoded_block"],
    recovered_bits=primary_result["recovered_bits"],
    decoded_text=primary_result.get("decoded_text"),
    message_qubits=message_qubits,
)

st.subheader("How your text became M quantum bits")
_render_encoding_preview(enc)

st.subheader("At a glance")
fid = float(primary_result["metrics"]["fidelity"])
bacc = float(primary_result["metrics"]["bitwise_accuracy"])
label, emoji = _recovery_story_badge(fid, bacc)

st.markdown(f"### {emoji} Outcome: **{label}**")
st.caption(
    f"Using “{_decoder_plain_name(primary_mode)}” as the main view. "
    "Lower scores usually mean stronger mixing or a harsher readout — not necessarily that “information vanished.”"
)

c1, c2, c3 = st.columns(3)
c1.metric("Your message", protocol["input_message"][:80] + ("…" if len(protocol["input_message"]) > 80 else ""))
c2.metric("Match quality (simple)", f"{bacc:.0%}", help="Fraction of bits that match the encoded block.")
c3.metric("Exact match?", "Yes" if fid >= 0.999 else "No")

st.progress(min(1.0, max(0.0, bacc)))
st.caption(f"Bit agreement: {bacc:.0%}")

st.markdown("**Side-by-side bits** (easier than equations):")
_render_bit_compare(protocol["encoded_block"], primary_result["recovered_bits"])

if primary_result.get("decoded_text") is not None:
    st.success(f"**As text (when possible):** {primary_result['decoded_text']!r}")
else:
    st.info(
        primary_result.get(
            "decode_note",
            "Recovered bits are not a full byte multiple, so we show bits instead of UTF-8 text.",
        )
    )

with st.expander("What each decoder means (for viewers)"):
    st.markdown(
        """
| Name in the app | Idea in plain English |
|-----------------|------------------------|
| **Quick readout** | After scrambling, pick the single most likely outcome and read your message bits from it. |
| **Ideal unscramble** | Apply the exact reverse of the scrambler. This is a **best-case** reference if the dynamics are known. |

**Tip for demos:** start with **Ideal unscramble** + low depth to show a clear success, then add **Quick readout** or noise to show how hard recovery becomes.
        """
    )

st.subheader("Primary Recovery Result (details)")
col1, col2, col3 = st.columns(3)
col1.metric("Primary decoder", _decoder_plain_name(primary_mode))
col2.metric("Fidelity", f"{primary_result['metrics']['fidelity']:.3f}")
col3.metric("Bitwise accuracy", f"{primary_result['metrics']['bitwise_accuracy']:.3f}")

st.subheader("Decoder Comparison")
rows = []
for mode, result in protocol["decoder_results"].items():
    rows.append(
        {
            "Friendly name": _decoder_plain_name(mode),
            "decoder_mode": mode,
            "fidelity": result["metrics"]["fidelity"],
            "success_probability": result["metrics"]["success_probability"],
            "bitwise_accuracy": result["metrics"]["bitwise_accuracy"],
            "recovered_bits": result["recovered_bits"],
            "decoded_text": result["decoded_text"],
        }
    )
decoder_df = pd.DataFrame(rows)
st.dataframe(decoder_df, use_container_width=True)

st.subheader("Stage-by-Stage Trace")
for stage in protocol["stages"]:
    with st.expander(f"{stage['title']} ({stage['stage']})", expanded=False):
        st.write(stage["description"])
        if show_expert_json:
            st.json(stage["data"])
        else:
            st.caption("Turn on “Show raw JSON in stages” in the sidebar to inspect full technical data.")

if run_noise:
    st.subheader("Noisy Simulator Sweep")
    try:
        p2_values = _parse_float_list(p2_values_raw)
    except ValueError:
        st.error("Invalid `p2` list. Use comma-separated floats.")
        p2_values = []

    if p2_values:
        sweep = run_depolarizing_noise_sweep(
            message=message,
            message_qubits=message_qubits,
            black_hole_qubits=black_hole_qubits,
            reference_qubits=reference_qubits,
            scramble_depth=scramble_depth,
            decoder_mode=primary_mode,
            p2_values=p2_values,
            p1_ratio=float(p1_ratio),
            shots=int(noise_shots),
        )

        sweep_rows = []
        for trial in sweep["trials"]:
            sweep_rows.append(
                {
                    "p2": trial["noise"]["p2"],
                    "p1": trial["noise"]["p1"],
                    "fidelity": trial["metrics"]["fidelity"],
                    "bitwise_accuracy": trial["metrics"]["bitwise_accuracy"],
                    "recovered_bits": trial["recovered_bits"],
                }
            )
        sweep_df = pd.DataFrame(sweep_rows).sort_values("p2")
        st.caption(
            "Noise makes gates imperfect — recovery often drops as noise increases, similar to how "
            "hardware experiments get harder as circuits get deeper."
        )
        st.dataframe(sweep_df, use_container_width=True)
        st.line_chart(sweep_df.set_index("p2")[["fidelity", "bitwise_accuracy"]])

if run_hardware:
    st.subheader("IBM Hardware Checkpoint (Opt-In)")
    if os.getenv(token_env_var, "") == "":
        st.warning(
            f"Environment variable `{token_env_var}` is not set in this shell. "
            "Set it before running hardware checkpoints."
        )
    else:
        with st.spinner("Submitting hardware checkpoint job..."):
            try:
                hw_result = run_ibm_hardware_checkpoint(
                    message=message,
                    message_qubits=message_qubits,
                    black_hole_qubits=black_hole_qubits,
                    reference_qubits=reference_qubits,
                    scramble_depth=scramble_depth,
                    decoder_mode=hardware_decoder,
                    shots=int(hardware_shots),
                    backend_name=backend_name.strip() or None,
                    token_env_var=token_env_var,
                )
                st.success("Hardware checkpoint completed.")
                st.json(hw_result)
            except Exception as exc:
                st.error(f"Hardware checkpoint failed: {exc}")
