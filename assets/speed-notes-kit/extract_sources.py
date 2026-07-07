#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把课件 PDF / 第三方笔记 docx / 往年题 PDF 预提取为纯文本，供写作 agent 直接读取（来自 autopku speed-notes-kit）。

为什么需要：写作 agent 直接对中文文件名/路径跑 pdftotext 偶有编码坑（macOS 上尤甚）；
预先由主控 agent 把所有源料 dump 成 .build/sources/*.txt（ASCII 文件名），
写作 agent 只读取纯文本，稳。

用法：改下面 CONFIG（CRS/OUT + 三张文件清单），`uv run python extract_sources.py` 或
`python3 extract_sources.py`（需 pymupdf、python-docx：`uv add pymupdf python-docx`）。
"""
import os, fitz, docx

# ===== CONFIG：按课程改 =====
CRS = '/ABSOLUTE/PATH/TO/课程'                       # 课程根目录
OUT = '/ABSOLUTE/PATH/TO/课程/讲义名/.build/sources'  # 输出纯文本目录
# 三张清单：(相对 CRS 的源文件路径, 输出 txt 文件名)。按本课实际填，不需要的留空 []。
slides = [
    # ('课件/第6讲 xxx.pdf', 'slide-L6.txt'),
]
notes = [
    # ('其他笔记/某笔记.docx', 'note-L6.txt'),
]
exams = [
    # ('往年题/某回忆版.pdf', 'exam-2021.txt'),
]
# ============================

os.makedirs(OUT, exist_ok=True)


def dump_pdf(src, dst, page_marks=True):
    d = fitz.open(src)
    buf = []
    for i, pg in enumerate(d):
        if page_marks:
            buf.append(f"\n----- [p{i+1}/{d.page_count}] -----\n")
        buf.append(pg.get_text())
    d.close()
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(''.join(buf))
    return os.path.getsize(dst)


def dump_docx(src, dst):
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    d = docx.Document(src)
    buf = []
    for child in d.element.body.iterchildren():     # 保留段落/表格原顺序
        if isinstance(child, CT_P):
            p = Paragraph(child, d)
            txt = p.text.rstrip()
            if txt:
                st = (p.style.name or '').lower()
                buf.append(f"\n### {txt}" if st.startswith('heading') else txt)
        elif isinstance(child, CT_Tbl):
            tb = Table(child, d)
            buf.append("\n[表格]")
            for row in tb.rows:
                buf.append(" | ".join(c.text.strip().replace('\n', ' ') for c in row.cells))
            buf.append("[/表格]\n")
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('\n'.join(buf))
    return os.path.getsize(dst)


if __name__ == '__main__':
    print("=== slides ===")
    for s, o in slides:
        print(f"  {o}  ({dump_pdf(os.path.join(CRS, s), os.path.join(OUT, o))} bytes)")
    print("=== notes ===")
    for s, o in notes:
        print(f"  {o}  ({dump_docx(os.path.join(CRS, s), os.path.join(OUT, o))} bytes)")
    print("=== exams ===")
    for s, o in exams:
        print(f"  {o}  ({dump_pdf(os.path.join(CRS, s), os.path.join(OUT, o), page_marks=False)} bytes)")
    print("DONE")
