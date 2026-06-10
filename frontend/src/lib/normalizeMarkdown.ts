/** Normalize assistant markdown before render (tables, formulas). */

const MATH_CMD =
  /\\(?:iint|iiint|int|frac|sqrt|cos|sin|tan|ln|log|left|right|Big|theta|pi|sigma|partial|cdot)/;

function collapseBrokenMathLines(text: string): string {
  let out = text;
  out = out.replace(/\\sqrt\{([^}]*)\}/g, (_, inner: string) => {
    const fixed = inner
      .replace(/\s*\n+\s*\+\s*\n+\s*/g, "+")
      .replace(/\s+/g, "")
      .replace(/\++/g, "+");
    return `\\sqrt{${fixed}}`;
  });
  out = out.replace(
    /([a-zA-Z0-9\\}])\s*\n+\s*\+\s*\n+\s*([a-zA-Z0-9\\{])/g,
    "$1+$2"
  );
  out = out.replace(
    /([a-zA-Z])\s*\n+\s*(\d+)\s*\n+\s*\+\s*\n+\s*([a-zA-Z])\s*\n+\s*(\d+)/g,
    "$1^$2+$3^$4"
  );
  out = out.replace(/\\cos\^(\d+)\s*\n+\s*θ\s*\n+\s*θ/gi, "\\cos^$1\\theta");
  out = out.replace(/\\cos\^(\d+)\s*\n+\s*θ/gi, "\\cos^$1\\theta");
  return out;
}

function fixTrigAndTheta(text: string): string {
  let out = text;
  out = out.replace(/\\\$cos\^?(\d*)\$\\?theta/gi, "\\cos^$1\\theta");
  out = out.replace(/\\\$cos\^?(\d*)\$/gi, "\\cos^$1");
  out = out.replace(/\$\\?cos\^?(\d*)\$\\?theta/gi, "\\cos^$1\\theta");
  out = out.replace(/\$\\?cos\^?(\d*)\$/gi, "\\cos^$1");
  out = out.replace(/(?<!\\)\bcos(\^?\d*)/gi, "\\cos$1");
  out = out.replace(/(?<!\\)\bsin(\^?\d*)/gi, "\\sin$1");
  out = out.replace(/(?<!\\)θ/g, "\\theta");
  out = out.replace(/(\\theta\s*){2,}/g, "\\theta ");
  return out;
}

const RAW_LATEX =
  /\\(?:int|iint|frac|sqrt|left|right|infty|pi|theta|sigma|cos|sin)/;

function fixDifferentialSpacing(text: string): string {
  return text.replace(/,\s*(d[rθσ]|d\\(?:theta|sigma|r|x|y|t))/g, "\\, $1");
}

function fixFullWidthMathSymbols(text: string): string {
  return text
    .replace(/＋/g, "+")
    .replace(/－/g, "-")
    .replace(/−/g, "-")
    .replace(/×/g, "\\times ")
    .replace(/÷/g, "\\div ")
    .replace(/＝/g, "=")
    .replace(/（/g, "(")
    .replace(/）/g, ")")
    .replace(/∬/g, "\\iint ")
    .replace(/∫/g, "\\int ")
    .replace(/σ/g, "\\sigma ")
    .replace(/π/g, "\\pi ");
}

function fixBrokenStepHeadings(text: string): string {
  const step = "(?:第一|第二|第三|第四|第五|第六|第七|第八|第九|第十)步[：:]";
  return text.replace(new RegExp(`\\*\\*(${step}[^*\\n]+?)\\*\\*`, "g"), (_, title: string) => {
    const dollarCount = (title.match(/\$/g) || []).length;
    const fixedTitle = dollarCount % 2 === 1 ? `${title}$` : title;
    return `\n\n### ${fixedTitle}\n`;
  });
}

function splitLectureStructure(text: string): string {
  return text
    .replace(/(###\s*){2,}/g, "\n\n### ")
    .replace(/(##\s*){2,}/g, "\n\n## ")
    .replace(/---\s*##\$?\s*/g, "\n\n---\n\n## ")
    .replace(/---\s*\$\$/g, "\n\n---\n\n")
    .replace(/\$\$\s*---/g, "\n\n---")
    .replace(/\$\s*(?=##\s*题目\d+)/g, "\n\n")
    .replace(/\$\s*(?=###\s*)/g, "\n\n")
    .replace(/([^\n])(\s*##\s*题目\d+[：:])/g, "$1\n\n$2")
    .replace(/([^\n])(\s*###\s*(?:第[一二三四五六七八九十]+步|解题步骤))/g, "$1\n\n$2")
    .replace(/([^\n])(\s*\*\*答案[：:]\*\*)/g, "$1\n\n$2")
    .replace(/([^\n])(\s*\*\*结论\*\*[：:])/g, "$1\n\n$2")
    .replace(/([^\n])(\s*完整题型总结)/g, "$1\n\n$2")
    .replace(/([^\n])(\s*还需要继续)/g, "$1\n\n$2");
}

function fixUnclosedInlineDollars(text: string): string {
  return text
    .split("\n")
    .map((line) => {
      const dollarCount = (line.match(/\$/g) || []).length;
      return dollarCount % 2 === 1 ? `${line}$` : line;
    })
    .join("\n");
}

function protectMarkdownStructure(text: string): string {
  return text
    .replace(/---\$\$/g, "\n\n---\n\n")
    .replace(/\$\$\s*(?=(#{1,3}\s|题目\d+|完整题型总结|还需要|[-*]\s|\|))/g, "\n\n")
    .replace(/\s+(#{1,3}\s)/g, "\n\n$1")
    .replace(/\s+(题目\d+[：:])/g, "\n\n## $1")
    .replace(/\s+(完整题型总结)/g, "\n\n## $1")
    .replace(/\s+(\*\*?第[一二三四五六七八九十]+步[：:])/g, "\n\n$1")
    .replace(/\s+((?:第一|第二|第三|第四|第五|第六|第七|第八|第九|第十)步[：:])/g, "\n\n### $1")
    .replace(/\s+(\*\*答案[：:]\*\*)/g, "\n\n$1")
    .replace(/\s+(答案[：:])/g, "\n\n**$1** ")
    .replace(/\s+(\|[^\n]+\|)/g, "\n$1");
}

function isPureMathLine(t: string): boolean {
  if (/[\u4e00-\u9fff]/.test(t)) return false;
  if (/\*\*|#{1,3}\s|^[-*]\s/.test(t)) return false;
  return RAW_LATEX.test(t) || /^\\[a-zA-Z]/.test(t) || /^[\d=+\-]/.test(t);
}

function fixOrphanDollarLines(text: string): string {
  return text
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (!t || t.startsWith("$$") || !isPureMathLine(t)) return line;
      if (t.endsWith("$$") && !t.startsWith("$")) {
        return `$$${t.slice(0, -2).trim()}$$`;
      }
      if (t.endsWith("$") && !t.endsWith("$$") && !t.startsWith("$")) {
        return `$$${t.slice(0, -1).trim()}$$`;
      }
      if (t.startsWith("$") && !t.startsWith("$$") && !t.endsWith("$")) {
        return `$$${t.slice(1).trim()}$$`;
      }
      if (!t.includes("$")) {
        return `$$${t}$$`;
      }
      return line;
    })
    .join("\n");
}

function fixMismatchedDollars(text: string): string {
  return text
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (/^\$[^$].*\$\$$/.test(t)) return `$$${t.slice(1, -2).trim()}$$`;
      if (/^\$\$.*[^$]\$$/.test(t) && !t.endsWith("$$")) {
        return `$$${t.slice(2, -1).trim()}$$`;
      }
      return line;
    })
    .join("\n");
}

function stripSpuriousDollars(text: string): string {
  let out = text;
  for (let i = 0; i < 6; i += 1) {
    out = out.replace(/(\\[a-zA-Z]+[^{}$]*?)\$([^$\\]{1,40})\$/g, "$1$2");
  }
  out = out.replace(/\$([rs])(\^[0-9]+)\$/gi, "$1$2");
  out = out.replace(/\\\$/g, "");
  return out;
}

function normalizeLatexChunk(chunk: string, keepLeadingEq = false): string {
  let s = chunk.trim().replace(/^\$+|\$+$/g, "");
  const textCut = s.search(/[\u4e00-\u9fff]|#{1,3}\s|\*\*/);
  if (textCut > 0) s = s.slice(0, textCut).trim();
  if (!keepLeadingEq) s = s.replace(/^[=＝]\s*/, "");
  s = collapseBrokenMathLines(s);
  s = fixTrigAndTheta(s);
  s = fixDifferentialSpacing(s);
  s = stripSpuriousDollars(s);
  s = s.replace(/\\{2,},/g, "\\,");
  s = s.replace(/\s+/g, " ");
  s = s.replace(/(?<!\\)Big\|/g, "\\Big|");
  return s;
}

function unwrapMixedDisplayMathBlocks(text: string): string {
  return text.replace(/\$\$([\s\S]*?)\$\$/g, (_, raw: string) => {
    const cleaned = raw
      .replace(/\\begin\{aligned\}/g, "")
      .replace(/\\end\{aligned\}/g, "")
      .trim();
    const mixed = /[\u4e00-\u9fff]|#{1,3}\s|\*\*|---|\|/.test(cleaned);
    if (!mixed) return `$$${cleaned}$$`;
    return protectMarkdownStructure(cleaned)
      .split("\n")
      .map((line) => {
        const t = line.trim();
        if (!t) return "";
        if (isPureMathLine(t)) return `$$${normalizeLatexChunk(t)}$$`;
        return t;
      })
      .join("\n");
  });
}

function splitAtDerivationEquals(latex: string): string[] {
  const parts: string[] = [];
  let buf = "";
  let depth = 0;
  for (let i = 0; i < latex.length; i += 1) {
    const c = latex[i];
    if (c === "{") depth += 1;
    else if (c === "}") depth = Math.max(0, depth - 1);
    if (depth === 0 && latex[i] === " " && latex.slice(i, i + 3) === " = ") {
      const next = latex[i + 3];
      if (next === "\\" || next === "-" || /\d/.test(next)) {
        if (buf.trim()) parts.push(buf.trim());
        buf = "";
        i += 2;
        continue;
      }
    }
    buf += c;
  }
  if (buf.trim()) parts.push(buf.trim());
  return parts.length > 1 ? parts : [latex.trim()];
}

function buildAlignedBlock(chunks: string[]): string {
  const rows: string[] = [];
  chunks.forEach((raw, idx) => {
    const s = raw.trim().replace(/^=\s*/, "");
    if (!s) return;
    if (idx === 0) {
      const eqAt = s.indexOf(" = ");
      if (eqAt > 0) {
        rows.push(`${s.slice(0, eqAt)} &= ${s.slice(eqAt + 3)}`);
      } else {
        rows.push(s);
      }
    } else {
      rows.push(`&= ${s}`);
    }
  });
  if (rows.length <= 1) {
    return `$$\n${rows[0] || chunks[0] || ""}\n$$`;
  }
  return `$$\n\\begin{aligned}\n${rows.join(" \\\\\n")}\n\\end{aligned}\n$$`;
}

type Segment = { type: "text" | "math"; content: string };

function splitMathSegments(text: string): Segment[] {
  const segments: Segment[] = [];
  const re = /\$\$([\s\S]*?)\$\$/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      segments.push({ type: "text", content: text.slice(last, m.index) });
    }
    segments.push({ type: "math", content: m[1].trim() });
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    segments.push({ type: "text", content: text.slice(last) });
  }
  return segments;
}

function formatDerivationsReadable(text: string): string {
  const segments = splitMathSegments(text);
  const out: string[] = [];
  let i = 0;

  while (i < segments.length) {
    if (segments[i].type === "text") {
      out.push(segments[i].content);
      i += 1;
      continue;
    }

    const chunks: string[] = [];
    while (i < segments.length) {
      if (segments[i].type === "math") {
        chunks.push(normalizeLatexChunk(segments[i].content, chunks.length > 0));
        i += 1;
        continue;
      }
      if (!segments[i].content.trim()) {
        if (segments[i + 1]?.type === "math") {
          i += 1;
          continue;
        }
      }
      break;
    }

    if (chunks.length === 1) {
      const sub = splitAtDerivationEquals(chunks[0]);
      out.push(sub.length > 1 ? buildAlignedBlock(sub) : `$$\n${chunks[0]}\n$$`);
    } else if (chunks.length > 1) {
      out.push(buildAlignedBlock(chunks));
    }
    out.push("\n");
  }

  return out.join("");
}

function isChineseLeadLine(line: string): boolean {
  const t = line.trim();
  return /^[\u4e00-\u9fff]/.test(t) || /^(由于|因为|所以|其中|设|令|故|则|答|解)/.test(t);
}

function isMathContinuation(line: string): boolean {
  const t = line.trim();
  if (!t) return false;
  if (/[\u4e00-\u9fff]/.test(t) || /^\*\*|^#{1,3}\s/.test(t)) return false;
  if (t === "+" || t === "=" || t.startsWith("=")) return true;
  if (MATH_CMD.test(t)) return true;
  if (/^\\[a-zA-Z]/.test(t)) return true;
  if (/^[\d\\]/.test(t) && /[\\^_{}]/.test(t)) return true;
  if (RAW_LATEX.test(t)) return true;
  return false;
}

function wrapDisplayMathBlocks(text: string): string {
  const lines = text.split("\n");
  const out: string[] = [];
  let buf: string[] = [];

  const flush = () => {
    if (!buf.length) return;
    const merged = normalizeLatexChunk(buf.join(" "));
    if (merged) out.push(`$$${merged}$$`);
    buf = [];
  };

  for (const line of lines) {
    const t = line.trim();
    if (!t) {
      flush();
      out.push("");
      continue;
    }
    if (t.startsWith("$$") && t.endsWith("$$") && t.length > 4) {
      flush();
      out.push(`$$${normalizeLatexChunk(t.slice(2, -2))}$$`);
      continue;
    }
    if (isChineseLeadLine(t)) {
      flush();
      let fixed = fixTrigAndTheta(stripSpuriousDollars(t));
      fixed = fixed.replace(
        /(\\(?:cos|sin|tan|theta|pi)(?:\^?\{?[^}\s，。；：]+)?)/gi,
        (m) => `$${m}$`
      );
      out.push(fixed);
      continue;
    }
    if (t.startsWith("=") && buf.length > 0) {
      flush();
      buf.push(t);
      continue;
    }
    if (isMathContinuation(t) || (buf.length > 0 && isMathContinuation(t))) {
      buf.push(t);
      continue;
    }
    flush();
    out.push(line);
  }
  flush();
  return out.join("\n");
}

function fixMarkdownTables(text: string): string {
  const lines = text.split("\n");
  const out: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const isRow = /^\s*\|.+\|\s*$/.test(line);
    if (!isRow) {
      out.push(line);
      i += 1;
      continue;
    }
    const block: string[] = [];
    while (i < lines.length && /^\s*\|.+\|\s*$/.test(lines[i])) {
      block.push(lines[i].trim());
      i += 1;
    }
    const cols = (block[0].match(/\|/g) || []).length - 1;
    const sep =
      "|" + Array.from({ length: Math.max(cols, 1) }, () => "------").join("|") + "|";
    if (block.length === 1 || !/^\|[\s\-:|]+\|$/.test(block[1])) {
      block.splice(1, 0, sep);
    }
    if (out.length && out[out.length - 1].trim() !== "") out.push("");
    out.push(...block, "");
  }
  return out.join("\n");
}

function fixInlineSummaryTables(text: string): string {
  return text.replace(
    /完整题型总结\s*\|([\s\S]*?)(?=\n---|\n还需要|$)/g,
    (_, table: string) => {
      const cells = table
        .split("|")
        .map((cell) => cell.trim())
        .filter((cell) => cell && !/^-+$/.test(cell));
      const rows: string[] = ["## 完整题型总结"];
      for (let i = 0; i < cells.length; i += 3) {
        const row = cells.slice(i, i + 3);
        if (row.length === 3) rows.push(`| ${row.join(" | ")} |`);
      }
      return rows.join("\n");
    }
  );
}

function rescueTextFromMathBlocks(text: string): string {
  return text.replace(/\$\$([\s\S]*?)\$\$/g, (_, raw: string) => {
    if (!/[\u4e00-\u9fff]|#{2,4}\s|\*\*答案/.test(raw)) return `$$${raw}$$`;
    const out: string[] = [];
    let math: string[] = [];
    const flushMath = () => {
      const kept = math.map((line) => line.trim()).filter(Boolean);
      if (kept.length) out.push(`$$\n${kept.join("\n")}\n$$`);
      math = [];
    };
    const expanded = raw.replace(/\s+&=\s+(?=#{2,4}\s|\*\*)/g, "\n");
    for (const line of expanded.split("\n")) {
      const t = line.trim();
      if (!t) continue;
      if (/[\u4e00-\u9fff]|#{2,4}\s|\*\*答案/.test(t)) {
        flushMath();
        out.push(
          t
            .replace(/^&=\s*/, "")
            .replace(/^####\s*/, "### ")
            .replace(/\\\\\s*&=\s*/g, "=")
            .trim()
        );
      } else {
        math.push(t);
      }
    }
    flushMath();
    return out.join("\n\n");
  });
}

function cleanMarkdownArtifacts(text: string): string {
  return text
    .replace(/\\begin\{aligned\}\s*(\*\*答案[\s\S]*?)\\end\{aligned\}/g, "$1")
    .replace(/##\s+##/g, "##")
    .replace(/###\s+###/g, "###")
    .replace(/^####\s+/gm, "### ")
    .replace(/^\s*#{1,3}\s*$/gm, "")
    .replace(/\$\$\s*\$\$/g, "")
    .replace(/---\$\$/g, "---")
    .replace(/\\begin\{aligned\}(?=[\s\S]*?(#{1,4}\s|\*\*答案|[\u4e00-\u9fff]))/g, "")
    .replace(/\\end\{aligned\}/g, "")
    .replace(/\\\s*&=/g, "=")
    .replace(/\\{2,}\s*(?=###|##|\*\*)/g, "")
    .replace(/^(\*\*答案[：:]\*\*.*)$/gm, (line) =>
      line.replace(/\\\\\s*&=\s*/g, "=").replace(/\s+/g, " ").trim()
    );
}

function fixDanglingMathFragments(text: string): string {
  return text
    .replace(/\$\$\s*\\end\{aligned\}\s*\$\$/g, "")
    .replace(/\$\$\s*\\begin\{aligned\}\s*\$\$/g, "")
    .replace(/\\begin\{aligned\}\s*\$\$/g, "")
    .replace(/\$\$\s*\\end\{aligned\}/g, "$$")
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (t.startsWith("\\begin{aligned}") && t.endsWith("\\end{aligned}")) {
        return `$$\n${t}\n$$`;
      }
      if (t.startsWith("\\begin{aligned}")) {
        return `$$\n${t}\\end{aligned}\n$$`;
      }
      if (!line.includes("**答案")) return line;
      const dollarCount = (line.match(/\$/g) || []).length;
      return dollarCount % 2 === 1 ? `${line}$` : line;
    })
    .join("\n");
}

function wrapRawAlignedMathLines(text: string): string {
  const out: string[] = [];
  let inDisplay = false;
  for (const line of text.split("\n")) {
    const t = line.trim();
    if (t === "$$") {
      inDisplay = !inDisplay;
      out.push(line);
      continue;
    }
    if (!inDisplay && t && !/[\u4e00-\u9fff]/.test(t) && (t.includes("&=") || /\\=/.test(t)) && RAW_LATEX.test(t)) {
      out.push(`$$\n\\begin{aligned}${t.replace(/\\=/g, "\\\\&=")}\\end{aligned}\n$$`);
    } else {
      out.push(line);
    }
  }
  return out.join("\n");
}

export function normalizeMarkdown(content: string): string {
  if (!content) return "";
  let text = content.replace(/\r\n/g, "\n");
  text = splitLectureStructure(text);
  text = fixBrokenStepHeadings(text);
  text = protectMarkdownStructure(text);
  text = fixUnclosedInlineDollars(text);
  text = fixFullWidthMathSymbols(text);
  text = fixMismatchedDollars(text);
  text = fixOrphanDollarLines(text);
  text = fixDifferentialSpacing(text);
  text = collapseBrokenMathLines(text);
  text = fixTrigAndTheta(text);
  text = stripSpuriousDollars(text);
  text = unwrapMixedDisplayMathBlocks(text);
  text = fixMismatchedDollars(text);
  text = fixOrphanDollarLines(text);
  text = wrapDisplayMathBlocks(text);
  text = formatDerivationsReadable(text);
  text = rescueTextFromMathBlocks(text);
  text = fixMismatchedDollars(text);
  text = fixOrphanDollarLines(text);
  text = fixMarkdownTables(text);
  text = fixInlineSummaryTables(text);
  text = text.replace(/\$\$\s*---\s*\$\$/g, "---");
  text = cleanMarkdownArtifacts(text);
  text = fixDanglingMathFragments(text);
  text = wrapRawAlignedMathLines(text);
  text = fixUnclosedInlineDollars(text);
  return text.replace(/\n{3,}/g, "\n\n").trim();
}
