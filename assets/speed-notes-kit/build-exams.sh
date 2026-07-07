#!/bin/bash
# 单文档批量构建脚本（来自 autopku speed-notes-kit）
# 适用：往年题详解 / 任何「一份 MD -> 一份同名 PDF」的单文档（非分章讲义）场景。
# 用 ctexart（无 chapter）+ exam-preamble.tex。与 build.sh 共用 preprocess.py 和 callout.lua。
# 用法：拷到 .build/，改 CONFIG，再 `bash .build/build-exams.sh`
set -e

# ===== CONFIG：拷贝后改这几行 =====
ROOT="/ABSOLUTE/PATH/TO/课程"             # 课程根
SRCDIR="$ROOT/往年题（回忆版）"            # 待编译 MD 所在目录
PATTERN="*-订正版.md"                      # 匹配哪些 MD（每份编译成同名 PDF）
B="$ROOT/讲义名/.build"                    # 本 kit 所在 .build 目录
FONTSET="mac"                              # ctex 字体集，按系统选：mac / windows / ubuntu / fandol
# ==================================

STAGE="$B/exam-staging"
rm -rf "$STAGE"; mkdir -p "$STAGE"

cd "$B"
shopt -s nullglob
found=0
for f in "$SRCDIR"/$PATTERN; do
  found=1
  base="$(basename "$f" .md)"
  cp "$f" "$STAGE/$base.md"
  python3 "$B/preprocess.py" "$STAGE/$base.md" >/dev/null
  pandoc \
    "$STAGE/$base.md" \
    -f markdown+lists_without_preceding_blankline \
    --pdf-engine=xelatex \
    -V documentclass=ctexart \
    -V classoption=fontset=$FONTSET \
    --include-in-header="$B/exam-preamble.tex" \
    --lua-filter="$B/callout.lua" \
    -V colorlinks=true -V linkcolor=blue -V urlcolor=blue \
    --syntax-highlighting=idiomatic \
    -o "$SRCDIR/$base.pdf"
  echo "OK -> $SRCDIR/$base.pdf"
done
[ "$found" = 1 ] || { echo "没有匹配 $PATTERN 的 MD"; exit 1; }

rm -rf "$STAGE"
echo "ALL_OK"
