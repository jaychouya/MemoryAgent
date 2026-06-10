"""Normalize agent math/markdown output for human-readable rendering."""
import re

RAW_LATEX = re.compile(r"\\(?:int|iint|frac|sqrt|left|right|infty|pi|theta|sigma|cos|sin)")

_FULLWIDTH = str.maketrans({
    "＋": "+", "－": "-", "−": "-", "×": r"\times ", "÷": r"\div ",
    "＝": "=", "（": "(", "）": ")",
    "∬": r"\iint ", "∫": r"\int ", "σ": r"\sigma ", "π": r"\pi ",
})


def _fix_fullwidth(text: str) -> str:
    return text.translate(_FULLWIDTH)


def _fix_broken_step_headings(text: str) -> str:
    step = r"(?:第一|第二|第三|第四|第五|第六|第七|第八|第九|第十)步[：:]"

    def repl(match: re.Match) -> str:
        title = match.group(1)
        if title.count("$") % 2 == 1:
            title += "$"
        return f"\n\n### {title}\n"

    return re.sub(rf"\*\*({step}[^*\n]+?)\*\*", repl, text)


def _split_lecture_structure(text: str) -> str:
    text = re.sub(r"(###\s*){2,}", "\n\n### ", text)
    text = re.sub(r"(##\s*){2,}", "\n\n## ", text)
    text = re.sub(r"---\s*##\$?\s*", "\n\n---\n\n## ", text)
    text = re.sub(r"---\s*\$\$", "\n\n---\n\n", text)
    text = re.sub(r"\$\$\s*---", "\n\n---", text)
    text = re.sub(r"\$\s*(?=##\s*题目\d+)", "\n\n", text)
    text = re.sub(r"\$\s*(?=###\s*)", "\n\n", text)
    text = re.sub(r"([^\n])(\s*##\s*题目\d+[：:])", r"\1\n\n\2", text)
    text = re.sub(r"([^\n])(\s*###\s*(?:第[一二三四五六七八九十]+步|解题步骤))", r"\1\n\n\2", text)
    text = re.sub(r"([^\n])(\s*\*\*答案[：:]\*\*)", r"\1\n\n\2", text)
    text = re.sub(r"([^\n])(\s*\*\*结论\*\*[：:])", r"\1\n\n\2", text)
    text = re.sub(r"([^\n])(\s*完整题型总结)", r"\1\n\n\2", text)
    text = re.sub(r"([^\n])(\s*还需要继续)", r"\1\n\n\2", text)
    return text


def _fix_unclosed_inline_dollars(text: str) -> str:
    out = []
    for line in text.split("\n"):
        if line.count("$") % 2 == 1:
            line += "$"
        out.append(line)
    return "\n".join(out)


def _protect_markdown_structure(text: str) -> str:
    text = re.sub(r"---\$\$", "\n\n---\n\n", text)
    text = re.sub(r"\$\$\s*(?=(#{1,3}\s|题目\d+|完整题型总结|还需要|[-*]\s|\|))", "\n\n", text)
    text = re.sub(r"\s+(#{1,3}\s)", r"\n\n\1", text)
    text = re.sub(r"\s+(题目\d+[：:])", r"\n\n## \1", text)
    text = re.sub(r"\s+(完整题型总结)", r"\n\n## \1", text)
    text = re.sub(r"\s+(\*\*?第[一二三四五六七八九十]+步[：:])", r"\n\n\1", text)
    text = re.sub(r"\s+((?:第一|第二|第三|第四|第五|第六|第七|第八|第九|第十)步[：:])", r"\n\n### \1", text)
    text = re.sub(r"\s+(\*\*答案[：:]\*\*)", r"\n\n\1", text)
    text = re.sub(r"\s+(答案[：:])", r"\n\n**\1** ", text)
    text = re.sub(r"\s+(\|[^\n]+\|)", r"\n\1", text)
    return text


def _fix_differential(text: str) -> str:
    text = re.sub(r",\s*(d[rθσ]|d\\(?:theta|sigma|r|x|y|t))", r"\\, \1", text)
    text = re.sub(r"(?<=[^\s\\])d\\sigma\b", r"\\, d\\sigma", text)
    text = re.sub(r"(?<=[^\s\\])dσ\b", r"\\, d\\sigma", text)
    return text


def _fix_trig(text: str) -> str:
    text = re.sub(r"\\\$cos\^?(\d*)\$\\?theta", r"\\cos^\1\\theta", text, flags=re.I)
    text = re.sub(r"\\\$cos\^?(\d*)\$", r"\\cos^\1", text, flags=re.I)
    text = re.sub(r"(?<!\\)\bcos(\^?\d*)", r"\\cos\1", text, flags=re.I)
    text = text.replace("θ", r"\theta")
    return text


def _fix_mismatched_dollars(text: str) -> str:
    out = []
    for line in text.split("\n"):
        t = line.strip()
        if re.match(r"^\$[^$].*\$\$$", t):
            out.append(f"$${t[1:-2].strip()}$$")
        elif re.match(r"^\$\$.*[^$]\$$", t) and not t.endswith("$$"):
            out.append(f"$${t[2:-1].strip()}$$")
        else:
            out.append(line)
    return "\n".join(out)


def _is_pure_math_line(t: str) -> bool:
    if re.search(r"[\u4e00-\u9fff]", t):
        return False
    if re.search(r"\*\*|#{1,3}\s", t) or re.match(r"^[-*]\s", t):
        return False
    return bool(RAW_LATEX.search(t)) or t.startswith("\\") or t[0:1].isdigit() or t.startswith("=")


def _fix_orphan_dollar_lines(text: str) -> str:
    out = []
    for line in text.split("\n"):
        t = line.strip()
        if not t or t.startswith("$$") or not _is_pure_math_line(t):
            out.append(line)
            continue
        if t.endswith("$$") and not t.startswith("$"):
            out.append(f"$${t[:-2].strip()}$$")
        elif t.endswith("$") and not t.endswith("$$") and not t.startswith("$"):
            out.append(f"$${t[:-1].strip()}$$")
        elif t.startswith("$") and not t.startswith("$$") and not t.endswith("$"):
            out.append(f"$${t[1:].strip()}$$")
        elif "$" not in t:
            out.append(f"$${t}$$")
        else:
            out.append(line)
    return "\n".join(out)


def _unwrap_mixed_display_math(text: str) -> str:
    def repl(match: re.Match) -> str:
        cleaned = (
            match.group(1)
            .replace(r"\begin{aligned}", "")
            .replace(r"\end{aligned}", "")
            .strip()
        )
        if not re.search(r"[\u4e00-\u9fff]|#{1,3}\s|\*\*|---|\|", cleaned):
            return f"$${cleaned}$$"
        cleaned = _protect_markdown_structure(cleaned)
        out = []
        for line in cleaned.split("\n"):
            t = line.strip()
            if not t:
                out.append("")
            elif _is_pure_math_line(t):
                out.append(f"$${t}$$")
            else:
                out.append(t)
        return "\n".join(out)

    return re.sub(r"\$\$([\s\S]*?)\$\$", repl, text)


def _clean_markdown_artifacts(text: str) -> str:
    text = re.sub(r"\\begin\{aligned\}\s*(\*\*答案[\s\S]*?)\\end\{aligned\}", r"\1", text)
    text = re.sub(r"##\s+##", "##", text)
    text = re.sub(r"###\s+###", "###", text)
    text = re.sub(r"^####\s+", "### ", text, flags=re.M)
    text = re.sub(r"^\s*#{1,3}\s*$", "", text, flags=re.M)
    text = re.sub(r"\$\$\s*\$\$", "", text)
    text = text.replace("---$$", "---")
    text = re.sub(r"\\begin\{aligned\}(?=[\s\S]*?(#{1,4}\s|\*\*答案|[\u4e00-\u9fff]))", "", text)
    text = text.replace(r"\end{aligned}", "")
    text = re.sub(r"\\\s*&=", "=", text)
    text = re.sub(r"\\{2,}\s*(?=###|##|\*\*)", "", text)
    text = re.sub(
        r"^(\*\*答案[：:]\*\*.*)$",
        lambda m: re.sub(r"\s+", " ", m.group(1).replace(r"\\ &=", "=")).strip(),
        text,
        flags=re.M,
    )
    return text


def _rescue_text_from_math_blocks(text: str) -> str:
    def repl(match: re.Match) -> str:
        raw = match.group(1)
        if not re.search(r"[\u4e00-\u9fff]|#{2,4}\s|\*\*答案", raw):
            return f"$${raw}$$"
        out = []
        math = []

        def flush_math() -> None:
            kept = [line.strip() for line in math if line.strip()]
            if kept:
                out.append("$$\n" + "\n".join(kept) + "\n$$")
            math.clear()

        expanded = re.sub(r"\s+&=\s+(?=#{2,4}\s|\*\*)", "\n", raw)
        for line in expanded.split("\n"):
            t = line.strip()
            if not t:
                continue
            if re.search(r"[\u4e00-\u9fff]|#{2,4}\s|\*\*答案", t):
                flush_math()
                t = re.sub(r"^&=\s*", "", t)
                t = re.sub(r"^####\s*", "### ", t)
                t = t.replace(r"\\ &=", "=").strip()
                out.append(t)
            else:
                math.append(t)
        flush_math()
        return "\n\n".join(out)

    return re.sub(r"\$\$([\s\S]*?)\$\$", repl, text)


def _fix_dangling_math_fragments(text: str) -> str:
    text = re.sub(r"\$\$\s*\\end\{aligned\}\s*\$\$", "", text)
    text = re.sub(r"\$\$\s*\\begin\{aligned\}\s*\$\$", "", text)
    text = re.sub(r"\\begin\{aligned\}\s*\$\$", "", text)
    text = re.sub(r"\$\$\s*\\end\{aligned\}", "$$", text)
    out = []
    for line in text.split("\n"):
        t = line.strip()
        if t.startswith(r"\begin{aligned}") and t.endswith(r"\end{aligned}"):
            out.append("$$\n" + t + "\n$$")
            continue
        if t.startswith(r"\begin{aligned}"):
            out.append("$$\n" + t + r"\end{aligned}" + "\n$$")
            continue
        if "**答案" in line and line.count("$") % 2 == 1:
            line += "$"
        out.append(line)
    return "\n".join(out)


def _wrap_raw_aligned_math_lines(text: str) -> str:
    out = []
    in_display = False
    for line in text.split("\n"):
        t = line.strip()
        if t == "$$":
            in_display = not in_display
            out.append(line)
            continue
        if not in_display and t and not re.search(r"[\u4e00-\u9fff]", t) and ("&=" in t or r"\=" in t) and RAW_LATEX.search(t):
            t = t.replace(r"\=", r"\\&=")
            out.append("$$\n" + r"\begin{aligned}" + t + r"\end{aligned}" + "\n$$")
        else:
            out.append(line)
    return "\n".join(out)


def normalize_agent_output(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"(?is)<tool_call>.*?</tool_call>", "", text)
    text = _split_lecture_structure(text)
    text = _fix_broken_step_headings(text)
    text = _protect_markdown_structure(text)
    text = _fix_unclosed_inline_dollars(text)
    text = _fix_fullwidth(text)
    text = _fix_mismatched_dollars(text)
    text = _fix_orphan_dollar_lines(text)
    text = _fix_differential(text)
    text = _fix_trig(text)
    text = _unwrap_mixed_display_math(text)
    text = _fix_mismatched_dollars(text)
    text = _fix_orphan_dollar_lines(text)
    text = re.sub(r"\$\$\s*---\s*\$\$", "---", text)
    text = _rescue_text_from_math_blocks(text)
    text = _fix_mismatched_dollars(text)
    text = _fix_orphan_dollar_lines(text)
    text = _clean_markdown_artifacts(text)
    text = _fix_dangling_math_fragments(text)
    text = _wrap_raw_aligned_math_lines(text)
    text = _fix_unclosed_inline_dollars(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
