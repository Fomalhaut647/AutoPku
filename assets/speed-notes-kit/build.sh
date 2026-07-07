#!/bin/bash
# 速通讲义构建脚本（来自 autopku speed-notes-kit）
# 用法：把整个 kit 拷到 <课程>/<讲义名>/.build/，改下面 CONFIG，再 `bash .build/build.sh`
# 依赖：pandoc + xelatex(ctex) + python3。notes/ 下章节按 00-,01-,...,NN- 数字前缀命名控制拼接顺序。
set -e

# ===== CONFIG：拷贝后改这几行 =====
ROOT="/ABSOLUTE/PATH/TO/课程/讲义名"      # 讲义项目根（其下有 notes/ 和 .build/）
OUT="$ROOT/讲义.pdf"                       # 输出 PDF 路径与名字
FONTSET="mac"                              # ctex 字体集，按系统选：mac / windows / ubuntu / fandol
# ==================================

B="$ROOT/.build"
NOTES="$ROOT/notes"
STAGE="$B/staging"

rm -rf "$STAGE"; mkdir -p "$STAGE"
cp "$NOTES"/*.md "$STAGE"/
python3 "$B/preprocess.py" "$STAGE"/*.md >/dev/null

cd "$B"   # 让相对路径生效

# 第一个输入是 metadata.yaml（封面），后接 staging/ 里 00-,01-,... 按文件名排序的章节
pandoc \
  "$B/metadata.yaml" \
  "$STAGE"/[0-9][0-9]-*.md \
  -f markdown+lists_without_preceding_blankline \
  --pdf-engine=xelatex \
  -V documentclass=ctexrep \
  -V classoption=fontset=$FONTSET \
  --top-level-division=chapter \
  --include-in-header="$B/preamble.tex" \
  --lua-filter="$B/callout.lua" \
  --toc --toc-depth=2 \
  -V colorlinks=true -V linkcolor=blue -V toccolor=black -V urlcolor=blue \
  --syntax-highlighting=idiomatic \
  -o "$OUT"

rm -rf "$STAGE"
echo "BUILD_OK -> $OUT"
