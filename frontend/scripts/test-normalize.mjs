import { createRequire } from "module";
import { execSync } from "child_process";
import { writeFileSync, unlinkSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const dir = dirname(fileURLToPath(import.meta.url));
const tmp = join(dir, "_run_normalize.ts");
const src = join(dir, "../src/lib/normalizeMarkdown.ts");

const samples = [
  String.raw`2\pi \int_0^{+\infty} re^{-r^2} , dr = 2\pi \left[-\frac{1}{2}e^{-r^2}\right]_0^{+\infty}$`,
  String.raw`$\iint_D \frac{1}{\sqrt{x^2+y^2}} \, d\sigma = \int_0^{\pi/2} d\theta \int_1^2 \frac{1}{r} \cdot r \, dr$$`,
  String.raw`## 题目7：二重积分求体积

**题目：** 求体积

$$V = \iint_D [4 - (x^2 + y^2)] \, d\sigma$$

$$= \int_0^{2\pi} d\theta \int_0^2 (4 - r^2) \cdot r \, dr$$

$$= 8\pi$$

**答案：** $V = 8\pi$`,
  String.raw`机变量 (X,Y) 的联合概率密度为： f(x,y) = \begin{cases} kxy & 0 \leq x \leq 1, \, 0 \leq y \leq 1 \\ 0 & \text{其他} \end{cases}$$ \begin{aligned} 求常数k及 P(X+Y \leq 1) ### 解题步骤 第一步：求常数k 由概率密度的性质：\iint_{\mathbb{R}^2} f(x,y) \\, d\sigma \ &= 1 \end{aligned}

\int_0^1 dx \int_0^1 kxy \, dy = k \int_0^1 x \, dx \int_0^1 y \, dy = k \cdot \frac{1}{2} \cdot \frac{1}{2} = \frac{k}{4} = 1$$ 所以 $k=4$ **第二步：求 $P(X+Y \leq 1)** 积分区域D：x+y \leq 1，x \geq 0，y \geq 0
P(X+Y \leq 1) = \iint_D 4xy \\, d\sigma = 4\int_0^1 dx \int_0^{1-x} xy , dy$$

4\int_0^1 x \cdot \frac{y^2}{2}\Big|_0^{1-x} dx = 2\int_0^1 x(1-x)^2 \, dx$$
2\int_0^1 (x-2x^2+x^3) , dx = 2\left[\frac{x^2}{2}-\frac{2x^3}{3}+\frac{x^4}{4}\right]_0^1$$

2\left(\frac{1}{2}-\frac{2}{3}+\frac{1}{4}\right) = 2 \times \frac{1}{12} = \frac{1}{6}$$ \begin{aligned} **答案：** $k=4$，$P(X+Y \leq 1) \\ &= \dfrac{1}{6} \end{aligned}
---$$

题目20：综合大题 计算 \iint_D \frac{x^2}{a^2} + \frac{y^2}{b^2} \\\\, d\sigma，其中D为 \dfrac{x^2}{a^2} + \dfrac{y^2}{b^2} \leq 1 ### 解题步骤 **第一步：广义极坐标变换** 令 x=ar\cos\theta，y=br\sin\theta
雅可比行列式：
J
=
a
b
r
完整题型总结 | 序号 | 题型 | 关键技巧 | |------|------|----------| | 19 | 概率应用 | 密度函数性质 | | 20 | 广义极坐标 | 椭圆域变换 |
---$$ 还需要继续讲解其他类型题目吗？`,
  String.raw`第一步：极坐标表示
F(t) \

### ### 第二步：变限积分求导F'(t) = 2\pi \cdot t f(t^2)**答案：** $F'(t) = 2\pi t f(t^2)$
## 题目22：二重积分的存在性 证明：\iint_D \frac{1}{\sqrt{x^2+y^2}} \\\\\, d\sigma 收敛，其中 D: x^2+y^2 \leq 1$ ### 解题步骤 ### ### 第一步：转化为极坐标\iint_D \frac{1}{\sqrt{x^2+y^2}} \\\\\, d\sigma = \int_0^{2\pi} d\theta \int_0^1 \frac{1}{r} \cdot r \\\\\, dr = \int_0^{2\pi} d\theta \int_0^1 1 \\\\\, dr ### 第二步：计算积分
\begin{aligned}2\pi \times 1 \&= 2\pi\end{aligned}

**结论**：积分存在且值为 $2\pi
## 题目23：二重积分的换元法 计算 \iint_D (x+y) \\\\\, d\sigma，其中D由 x+y=1，x+y=2，x-y=0，x-y=1 围成 ### 解题步骤 ### 第一步：变量替换 令 u=x+y，v=x-y$ 则 $x=\dfrac{u+v}{2}$，$y=\dfrac{u-v}{2}$ ### 第二步：计算雅可比行列式 J \\ &= \begin{vmatrix} \dfrac{\partial x}{\partial u} & \dfrac{\partial x}{\partial v} \\ \dfrac{\partial y}{\partial u} & \dfrac{\partial y}{\partial v} \end{vmatrix} \\ &= \begin{vmatrix} \dfrac{1}{2} & \dfrac{1}{2} \\ \dfrac{1}{2} & -\dfrac{1}{2} \end{vmatrix} \\ $$&= -\frac{1}{2}\end{aligned} $|J| = \dfrac{1}{2}$ ### 第三步：确定积分区域 $u$ 的范围：$1 \leq u \leq 2 v 的范围：0 \leq v \leq 1 ### 第四步：计算积分 $\iint_D (x+y) \\\\\, d\sigma = \int_1^2 du \int_0^1 u \cdot \frac{1}{2} \, dv = \frac{1}{2} \int_1^2 u \, du \int_0^1 dv= \frac{1}{2} \cdot \frac{u^2}{2}\Big|_1^2 \cdot 1 = \frac{1}{4} \times (4-1) = \frac{3}{4}**答案：** $\dfrac{3}{4}$---##$ ## 题目24：利用对称性简化计算`,
];

writeFileSync(
  tmp,
  `import { normalizeMarkdown } from "../src/lib/normalizeMarkdown";\n` +
    samples
      .map(
        (s, i) =>
          `const o${i} = normalizeMarkdown(${JSON.stringify(s)});\n` +
          `console.log("--- sample ${i} ---");\n` +
          `console.log(o${i});\n` +
          `if (!o${i}.includes("$$")) throw new Error("sample ${i}: no display math");\n` +
          `if (/[^\\\\], dr/.test(o${i})) throw new Error("sample ${i}: bad differential");\n` +
          `if (o${i}.includes("begin{aligned}")) console.log("  [aligned block OK]");\n` +
          `{ const m${i}=o${i}.match(/\\\\begin\\{aligned\\}([\\s\\S]*?)\\\\end\\{aligned\\}/); if(m${i}&&m${i}[1].includes("答案")) throw new Error("sample ${i}: answer inside math"); }\n` +
          `if (/\\\\$\\\\$[\\\\s\\\\S]*(###|完整题型总结|还需要)[\\\\s\\\\S]*\\\\$\\\\$/.test(o${i})) throw new Error("sample ${i}: text swallowed by math");\n` +
          `if (o${i}.includes("### ###") || o${i}.includes("---##") || o${i}.includes("---##$")) throw new Error("sample ${i}: bad structure markers");\n` +
          `if ((o${i}.match(/\\$/g)||[]).length % 2 !== 0) throw new Error("sample ${i}: unbalanced dollars");\n`
      )
      .join("\n") +
    `console.log("ALL OK");\n`
);

try {
  execSync(`npx --yes tsx ${tmp}`, { cwd: join(dir, ".."), stdio: "inherit" });
} finally {
  unlinkSync(tmp);
}
