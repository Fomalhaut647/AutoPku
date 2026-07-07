#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
渲染前防御性预处理：修复 pandoc + XeLaTeX + ctex 已知踩坑。
用法：python3 preprocess.py file1.md file2.md ...   （就地修改）

处理（依据多门课程讲义构建的实测踩坑沉淀，原理详见 sub-skills/tasks/write-notes.md 的「常见渲染问题」表）：
1. 保护围栏代码块 ```...``` 与行内代码 `...`，其内不动。
2. 字面 Unicode 数学符号：数学段($...$/$$...$$)内换裸命令，段外换 $...$ 包裹的命令。
3. 闭合 $ 紧跟数字会使闭合失效 → 数学段后若紧跟数字，插入空格。
4. _\mathbf{} / ^\mathcal{} 等下上标直接接字体命令编译失败 → _{\mathbf{}}。
5. ^\* / _\* 误转义 → ^* / _*。
6. 圈数字 ①②③ → (1)(2)(3)。
7. 非 frontmatter 的 ---/***/___ 独行分隔线（含 > 前缀）会被当 YAML 解析 → 删除。
8. 数学段 $...$ 内侧紧贴空格（如 `$= $`、`$ +x$`）→ pandoc 不认作数学、整行错位、宏漏成缺字
   （2026-06 ICS 讲义实测：`$= $ 首地址 $ + 8\cdot...$` 致 \cdot 漏成 U+22C5 缺字）→ 剥掉内侧前后空格。
9. agent 残留的 NUL/控制字符（早期自做 lint 留下的哨兵字节）→ 编译报「invalid character」→ 删除。
"""
import re
import sys

# 希腊字母
GREEK = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\varepsilon', 'ϵ': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta',
    'θ': r'\theta', 'ϑ': r'\vartheta', 'ι': r'\iota', 'κ': r'\kappa',
    'λ': r'\lambda', 'μ': r'\mu', 'ν': r'\nu', 'ξ': r'\xi',
    'π': r'\pi', 'ρ': r'\rho', 'σ': r'\sigma', 'ς': r'\varsigma',
    'τ': r'\tau', 'υ': r'\upsilon', 'φ': r'\varphi', 'ϕ': r'\phi',
    'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Φ': r'\Phi',
    'Ψ': r'\Psi', 'Ω': r'\Omega',
}
# 关系/运算/集合/逻辑符号
SYM = {
    '≤': r'\le', '≥': r'\ge', '≠': r'\ne', '±': r'\pm', '∓': r'\mp',
    '×': r'\times', '÷': r'\div', '⋅': r'\cdot', '·': r'\cdot',
    '∞': r'\infty', '∈': r'\in', '∉': r'\notin', '∋': r'\ni',
    '⊂': r'\subset', '⊆': r'\subseteq', '⊃': r'\supset', '⊇': r'\supseteq',
    '∪': r'\cup', '∩': r'\cap', '∅': r'\varnothing',
    '∀': r'\forall', '∃': r'\exists', '¬': r'\neg',
    '→': r'\to', '←': r'\leftarrow', '↦': r'\mapsto', '↔': r'\leftrightarrow',
    '⇒': r'\Rightarrow', '⟹': r'\implies', '⇔': r'\Leftrightarrow', '⟺': r'\iff',
    '↑': r'\uparrow', '↓': r'\downarrow',
    '∑': r'\sum', '∏': r'\prod', '∫': r'\int', '∂': r'\partial', '∇': r'\nabla',
    '√': r'\surd', '∝': r'\propto', '≈': r'\approx', '≡': r'\equiv',
    '∼': r'\sim', '≜': r'\triangleq', '≅': r'\cong',
    '∠': r'\angle', '⊥': r'\perp', '∥': r'\parallel',
    '⌈': r'\lceil', '⌉': r'\rceil', '⌊': r'\lfloor', '⌋': r'\rfloor',
    '⋯': r'\cdots', '…': r'\dots',
    '∖': r'\setminus', '⊕': r'\oplus', '⊗': r'\otimes',
    'ℝ': r'\mathbb{R}', 'ℕ': r'\mathbb{N}', 'ℤ': r'\mathbb{Z}', 'ℚ': r'\mathbb{Q}',
    '✓': r'\checkmark', '✔': r'\checkmark', '✗': r'\times', '✘': r'\times',
    '−': r'-',
}
SUP = {'²': '2', '³': '3', '¹': '1', '⁰': '0', '⁴': '4', '⁵': '5',
       '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', 'ⁿ': 'n'}
SUB = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5',
       '₆': '6', '₇': '7', '₈': '8', '₉': '9'}

MATHMAP = {**GREEK, **SYM}

CIRCLED = {}
_circ = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
for i, ch in enumerate(_circ):
    CIRCLED[ch] = f'({i+1})'


def in_math_replace(s):
    for u, t in MATHMAP.items():
        s = s.replace(u, t)
    for u, d in SUP.items():
        s = s.replace(u, '^{' + d + '}')
    for u, d in SUB.items():
        s = s.replace(u, '_{' + d + '}')
    # _\mathbf{x} -> _{\mathbf{x}}
    s = re.sub(r'([_^])\\(mathcal|mathbf|mathbb|mathrm|boldsymbol|mathfrak|mathsf|mathtt|operatorname)\{([^{}]*)\}',
               r'\1{\\\2{\3}}', s)
    # ^\*  ->  ^*
    s = s.replace(r'^\*', '^*').replace(r'_\*', '_*')
    return s


def out_math_replace(s):
    for u, t in {**MATHMAP}.items():
        s = s.replace(u, '$' + t + '$')
    for u, d in SUP.items():
        s = s.replace(u, r'\textsuperscript{' + d + '}')
    for u, d in SUB.items():
        s = s.replace(u, r'\textsubscript{' + d + '}')
    for u, t in CIRCLED.items():
        s = s.replace(u, t)
    return s


# 分词：把文本切成 [(kind, text)]，kind ∈ {code, math, text}
TOKEN_RE = re.compile(r'(`+)(.+?)\1|(\$\$.+?\$\$)|(\$[^$\n]+?\$)', re.DOTALL)


def fix_dollar_digit(block):
    """最终 pass：闭合数学段后紧跟数字会使 $ 闭合失效 → 插入空格。
    在此 pass 重新分词，故能覆盖 out_math_replace 新生成的 $...$（如 ≥→$\\ge$ 紧跟 95）。"""
    out, pos = [], 0
    for m in TOKEN_RE.finditer(block):
        if m.start() > pos:
            out.append(block[pos:m.start()])
        tok = m.group(0)
        out.append(tok)
        if m.group(3) is not None or m.group(4) is not None:  # 是数学段
            nxt = block[m.end():m.end() + 1]
            if nxt.isdigit():
                out.append(' ')
        pos = m.end()
    if pos < len(block):
        out.append(block[pos:])
    return ''.join(out)


_CJK_PUNCT = '。，、；：！？'


def _peel_trailing_cjk(inner):
    """剥离数学段尾部裸露的 CJK 标点（移到段外，避免数学字体缺字）。"""
    i = len(inner)
    while i > 0 and (inner[i - 1] in _CJK_PUNCT or inner[i - 1] in ' \t'):
        i -= 1
    return inner[:i], inner[i:].strip()


def _norm_math_core(raw_inner):
    """规整行内/独立数学段内容：剥尾部 CJK 标点 + 去掉内侧前导空格。
    pandoc 要求开 $ 后紧跟非空格、闭 $ 前是非空格，否则整段不解析为数学（如 `$= $`、`$ +x$`）。
    LaTeX 本身忽略数学内边缘空格，故 strip 不改语义、只修「不被识别」。"""
    core, tail = _peel_trailing_cjk(raw_inner)
    core = core.lstrip(' \t')
    return core, tail


def process_block(block):
    """处理一个非围栏文本块（可能跨行）。"""
    out = []
    pos = 0
    for m in TOKEN_RE.finditer(block):
        if m.start() > pos:
            out.append(('text', block[pos:m.start()]))
        if m.group(1) is not None:          # 行内代码
            out.append(('code', m.group(0)))
        elif m.group(3) is not None:        # $$...$$
            core, tail = _norm_math_core(m.group(3)[2:-2])
            if core:
                out.append(('math', '$$' + in_math_replace(core) + '$$'))
                if tail:
                    out.append(('text', tail))
            else:                            # 退化（全空格/标点）→ 原样当文本，勿生成空 $$
                out.append(('text', m.group(3)))
        elif m.group(4) is not None:        # $...$
            core, tail = _norm_math_core(m.group(4)[1:-1])
            if core:
                out.append(('math', '$' + in_math_replace(core) + '$'))
                if tail:
                    out.append(('text', tail))
            else:
                out.append(('text', m.group(4)))
        pos = m.end()
    if pos < len(block):
        out.append(('text', block[pos:]))

    # 对 text 段做 out-of-math 替换（可能新生成 $...$）；code/math 段保持
    parts = [out_math_replace(txt) if kind == 'text' else txt
             for kind, txt in out]
    # 最终统一修复「闭合 $ 紧跟数字」，覆盖新生成的数学段
    return fix_dollar_digit(''.join(parts))


def strip_control_chars(text):
    """删除 NUL 与非法控制字符（保留 \\t \\n）。
    多 agent 写作时偶有自做 lint 留下的哨兵字节（如 \\x00\\x01），XeLaTeX 会报
    『Text line contains an invalid character』而整体编译失败。"""
    return ''.join(ch for ch in text
                   if ch in '\t\n' or not (ord(ch) < 0x20 or ord(ch) == 0x7f
                                           or 0x80 <= ord(ch) <= 0x9f))


def strip_rules(text):
    """删除非 frontmatter 的 ---/***/___ 独行分隔线（含 > 前缀）。"""
    lines = text.split('\n')
    # 检测顶部 YAML frontmatter
    fm_end = -1
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                fm_end = i
                break
    out = []
    for idx, ln in enumerate(lines):
        if fm_end >= 0 and idx <= fm_end:
            out.append(ln)
            continue
        s = ln.strip()
        if re.fullmatch(r'(-{3,}|\*{3,}|_{3,})', s):
            continue  # 删除裸分隔线
        if re.fullmatch(r'>\s*(-{3,}|\*{3,}|_{3,})', s):
            out.append('>')  # blockquote 内分隔线降级为空 blockquote 行
            continue
        out.append(ln)
    return '\n'.join(out)


_BACKTICK_SPAN = re.compile(r'`([^`\n]+)`')


def strip_math_backticks(text):
    """去掉误把行内数学/LaTeX 宏包进反引号代码 span 的情况。
    pandoc 会把 `$...$` 当字面代码原样输出（裸露成源码），不渲染成公式。
    只在 span 内容确实是数学时拆掉反引号，普通行内代码不动。"""
    def repl(m):
        inner = m.group(1)
        s = inner.strip()
        # 已含 $...$（行内或多段）→ 去掉外层反引号，让 $ 正常生效
        if s.startswith('$') and s.endswith('$') and s.count('$') >= 2:
            return inner
        # 裸 LaTeX 宏（如 \boxed{...}、\min(...)）需数学模式 → 包成 $...$
        if re.match(r'^\\(boxed|min|max|sum|frac|tfrac|sqrt|bar|hat|mathbb|mathrm|text)\b', s):
            return '$' + inner + '$'
        return m.group(0)
    return _BACKTICK_SPAN.sub(repl, text)


def _convert_quotes_block(block):
    """把非围栏文本块里、文本区（避开行内代码/数学）的 ASCII 双引号 " 转成中文弯引号。
    pandoc smart 判断开/闭看前一字符（英文开引号前是空格），CJK 字后的 " 一律被判成
    闭引号 → 开引号也渲染成右引号 ”。改为按行内交替（实测每行 " 数恒为偶数、行内成对）
    确定性转成 U+201C（“）/ U+201D（”），smart 见不到 ASCII " 即不再误配。"""
    spans = [(m.start(), m.end()) for m in TOKEN_RE.finditer(block)]
    out, i, si, n, expect_open = [], 0, 0, len(block), True
    while i < n:
        if si < len(spans) and spans[si][0] == i:   # 跳过行内代码/数学段
            a, b = spans[si]
            out.append(block[a:b]); i, si = b, si + 1
            continue
        ch = block[i]
        if ch == '\n':
            expect_open = True; out.append(ch)
        elif ch == '"':
            out.append('“' if expect_open else '”')
            expect_open = not expect_open
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


def convert_cjk_quotes(text):
    """对全文做弯引号转换，围栏代码块 ```...``` 内不动。"""
    fence_re = re.compile(r'(^```.*?^```)', re.DOTALL | re.MULTILINE)
    return ''.join(p if p.startswith('```') else _convert_quotes_block(p)
                   for p in fence_re.split(text))


def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    text = strip_control_chars(text)
    text = strip_rules(text)
    text = strip_math_backticks(text)
    text = convert_cjk_quotes(text)
    # 按围栏代码块切分（```...```），围栏内不动
    fence_re = re.compile(r'(^```.*?^```)', re.DOTALL | re.MULTILINE)
    pieces = fence_re.split(text)
    out = []
    for p in pieces:
        if p.startswith('```'):
            out.append(p)
        else:
            out.append(process_block(p))
    new = ''.join(out)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        process_file(p)
        print(f'preprocessed: {p}')
