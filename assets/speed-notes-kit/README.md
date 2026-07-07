# speed-notes-kit — 课程速通讲义构建工具包

跨课通用、已硬化过的「Markdown → 中文数学 PDF」构建套件，从多门课程（概率统计 / 公共财政学 / 金融计量 / 凸优化等）的实测构建中沉淀去重而来。随 AutoPku 分发，使用时整体拷贝到课程目录，原件保持干净。

> 由 autopku 的「写笔记/讲义」流程使用，见 `../../sub-skills/tasks/write-notes.md`。
> 各类渲染坑的原理与排错说明见 write-notes.md 的「常见渲染问题」表（本 kit 的脚本是这些知识的可执行形态）。

## 文件清单

| 文件 | 作用 | 是否需改 |
|------|------|----------|
| `preprocess.py` | 渲染前防御性预处理（修字面 Unicode 符号、`$`后接数字、`_\mathbf`、圈数字、裸分隔线、数学段尾 CJK 标点、中文弯引号、数学被反引号包成代码 等 9+ 类坑） | 否（无课程相关内容） |
| `callout.lua` | `> [!tip]/[!note]/[!warning]/[!example]` → 彩色可跨页 tcolorbox；标题**与类型名同名或以其开头**时去重（避免「易错：易错（…）」重复，配合 STYLE_SPEC §5 的 callout 写法） | 否 |
| `preamble.tex` | 主讲义 LaTeX 导言区（ctexrep；字体/版式/页眉/关自动编号） | 改 1 行页眉课程名 |
| `exam-preamble.tex` | 单文档（真题详解等）导言区（ctexart，无 chapter） | 否 |
| `metadata.yaml` | 封面元数据 title/subtitle/author/date（第 1 页封面来源） | 改标题/作者/日期 |
| `build.sh` | 主讲义构建：notes 多章 → 一份 PDF | 改 CONFIG 几行 |
| `build-exams.sh` | 单文档批量构建：一份 MD → 一份同名 PDF | 改 CONFIG 几行 |
| `extract_sources.py` | 把课件 PDF/笔记 docx/真题 PDF 预提取成纯文本喂给写作 agent（避开中文文件名/路径的编码坑） | 改 CONFIG + 文件清单 |
| `STYLE_SPEC.template.md` | 给所有写作 agent 的共享规范模板（深度档位/文档模板/LaTeX 硬规则通用；记号/考情按课填） | 填 §1 §4 §6 |
| `reference/` | 两份**实例参考**（某金融计量课程沉淀）：`EXAM_FORMAT_SPEC.md` 演示「按考试题型重构例题」的规范怎么写，`UPDATE_SPEC.md` 演示「按考纲瘦身讲义」的更新规范怎么写。给你的课写同类规范时照此改编 | — |

## 新课从零出一份讲义的流程

1. **建项目目录**：`<课程>/<讲义名>/{notes,.build}/`。
2. **拷 kit**：把本目录所有文件（除 README）拷进 `<课程>/<讲义名>/.build/`。
3. **改配置**：`build.sh` 的 ROOT/OUT/FONTSET；`preamble.tex` 页眉课程名；`metadata.yaml` 标题/作者/日期；（用到真题详解再改 `build-exams.sh`）。
4. **填规范**：把 `STYLE_SPEC.template.md` 改名 `STYLE_SPEC.md`，补 §1 参考资料、§4 记号约定、§6 考情分析（先读往年题归纳考情）。
5.（可选）**预提取源料**：填 `extract_sources.py` 清单并跑，得 `.build/sources/*.txt`。
6. **写内容**：为每章派一个并行写作 agent（每个 agent 读 STYLE_SPEC + 本章源料）各写一章 `notes/NN-*.md`；导读 `00-*.md` 通常由主控 agent 亲自写（含考情分析）。各运行时的并行 agent 机制见 `../../sub-skills/runtime/`。
7. **构建**：`bash .build/build.sh`（讲义）/ `bash .build/build-exams.sh`（真题详解）。
8. **验证**：`pdfinfo X.pdf | grep Pages`（>0）+ `pdftotext` 抽文本查无 `\boxed`/`\frac` 残渣、无缺字。macOS 的 `mdls` 对新建 PDF 常返回 null，用 `pdfinfo`。

## 依赖

`pandoc` + `xelatex`(ctex, TeX Live) + `python3`。预提取另需 `pymupdf`、`python-docx`（如用 uv：`uv add pymupdf python-docx`）。

- **宏包**：本 kit 只用 TeX Live 常规发行版自带的宏包，已刻意避开 `enumitem`/`fvextra`/`newunicodechar`/`titlesec`（basic/精简安装常缺、且用户可能无 `tlmgr` 权限）。写作规范里也据此禁用它们。
- **字体（按系统改）**：`build.sh` 的 `FONTSET` 默认 `mac`，Windows 改 `windows`、Linux 改 `ubuntu` 或 `fandol`（跨平台）；`preamble.tex`/`exam-preamble.tex` 的等宽字体默认 `Menlo`（macOS），Windows 换 `Consolas`、Linux 换 `DejaVu Sans Mono`——等宽字体需覆盖希腊字母/数学符号，否则代码注释里的 α、≤ 等会缺字。
