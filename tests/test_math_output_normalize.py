"""Test math output normalization for human-readable rendering."""
from src.agent.output_format import normalize_agent_output

BROKEN_SAMPLES = [
    (
        r"2\pi \int_0^{+\infty} re^{-r^2} , dr = 2\pi \left[-\frac{1}{2}e^{-r^2}\right]_0^{+\infty}$",
        ["\\, dr", "$$", "\\int"],
    ),
    (
        r"$\iint_D \frac{1}{\sqrt{x^2+y^2}} \, d\sigma = \int_0^{\pi/2} d\theta \int_1^2 \frac{1}{r} \cdot r \, dr$$",
        ["$$", "\\iint", "\\, d\\sigma"],
    ),
    (
        r"\iint_D \sqrt{x^2\n+\ny^2} \, d\sigma = \frac{32}{9}",
        ["$$", "\\sqrt"],
    ),
    (
        "V=∬_D [4−(x^2+y^2)] dσ",
        ["\\iint", "+", "\\sigma"],
    ),
]


def test_orphan_dollar_wrapped():
    raw = BROKEN_SAMPLES[0][0]
    out = normalize_agent_output(raw)
    assert out.startswith("$$")
    assert out.endswith("$$")
    assert "\\, dr" in out
    assert ", dr" not in out.replace("\\, dr", "")


def test_mismatched_dollars_fixed():
    raw = BROKEN_SAMPLES[1][0]
    out = normalize_agent_output(raw)
    assert out.count("$$") >= 2
    assert "$$" in out
    assert "\\iint" in out


def test_fullwidth_symbols_fixed():
    raw = BROKEN_SAMPLES[3][0]
    out = normalize_agent_output(raw)
    assert "−" not in out
    assert "∬" not in out
    assert "\\iint" in out


def test_all_samples_have_valid_markers():
    for raw, markers in BROKEN_SAMPLES:
        out = normalize_agent_output(raw)
        assert out, f"empty output for {raw[:40]}"
        for m in markers:
            assert m in out, f"missing {m} in {out[:80]}"


def test_malformed_math_does_not_swallow_sections():
    raw = (
        r"f(x,y)=\begin{cases} kxy & 0 \leq x \leq 1 \\ 0 & \text{其他} \end{cases}$$ "
        r"\begin{aligned} 求常数k及 P(X+Y \leq 1) ### 解题步骤 第一步：求常数k "
        r"\iint_{\mathbb{R}^2} f(x,y) \\, d\sigma \ &= 1 \end{aligned}"
        "\n"
        r"\int_0^1 dx \int_0^1 kxy \, dy = \frac{k}{4} = 1$$ 所以 $k=4$ "
        r"**第二步：求 $P(X+Y \leq 1)** P(X+Y \leq 1)=\iint_D 4xy \\, d\sigma$$"
        "\n"
        r"2\left(\frac{1}{2}-\frac{2}{3}+\frac{1}{4}\right)=\frac{1}{6}$$ "
        r"\begin{aligned} **答案：** $k=4$，$P(X+Y \leq 1) \\ &= \dfrac{1}{6} \end{aligned} ---$$"
    )
    out = normalize_agent_output(raw)
    assert "### 解题步骤" in out
    assert "**答案" in out
    assert "---$$" not in out
    assert "###" not in _display_math_text(out)
    assert "答案" not in _display_math_text(out)


def _display_math_text(text: str) -> str:
    import re
    return "\n".join(re.findall(r"\$\$([\s\S]*?)\$\$", text))
