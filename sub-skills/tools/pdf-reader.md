---
name: autopku-tool-pdf-reader
description: PyMuPDF/pdfplumber 读取PDF，支持中文、表格提取、图片提取、安全扫描
---

# PDF Reader Skill

读取PDF文件的Python工具方法，支持中文，提供两种方案：高性能模式(PyMuPDF)和表格提取模式(pdfplumber)。

## 安装依赖

```bash
# 方案1: 安装全部（推荐）
pip install pdfplumber pymupdf

# 方案2: 仅高性能模式
pip install pymupdf

# 方案3: 仅表格提取模式
pip install pdfplumber
```

## 快速开始

### 方法1: PyMuPDF (推荐，速度最快)

```python
import fitz  # PyMuPDF

def read_pdf_pymupdf(pdf_path, pages=None):
    """
    使用 PyMuPDF 读取PDF文本

    Args:
        pdf_path: PDF文件路径
        pages: 指定页码列表，如 [0, 1, 2] 或 range(5)，None表示全部

    Returns:
        dict: {'total_pages': 总页数, 'text': {页码: 文本内容}}
    """
    doc = fitz.open(pdf_path)
    result = {'total_pages': len(doc), 'text': {}}

    page_range = pages if pages is not None else range(len(doc))

    for i in page_range:
        if 0 <= i < len(doc):
            result['text'][i + 1] = doc[i].get_text()

    doc.close()
    return result

# 使用示例
pdf_path = "/Users/moonshot/Desktop/桌面整理/项目/pku大四下/逻辑导论/lectures/2.一只麻雀与逻辑学的起源.pdf"

# 读取全部内容
content = read_pdf_pymupdf(pdf_path)
print(f"总页数: {content['total_pages']}")
print(content['text'][1])  # 打印第1页

# 读取指定页
content = read_pdf_pymupdf(pdf_path, pages=[0, 1, 2])  # 第1-3页

# 读取前5页
content = read_pdf_pymupdf(pdf_path, pages=range(5))
```

### 方法2: pdfplumber (表格提取更强)

```python
import pdfplumber

def read_pdf_pdfplumber(pdf_path, pages=None):
    """
    使用 pdfplumber 读取PDF文本和表格

    Args:
        pdf_path: PDF文件路径
        pages: 指定页码列表，如 [0, 1, 2]，None表示全部

    Returns:
        dict: {
            'total_pages': 总页数,
            'text': {页码: 文本内容},
            'tables': {页码: [表格数据]}
        }
    """
    result = {'total_pages': 0, 'text': {}, 'tables': {}}

    with pdfplumber.open(pdf_path) as pdf:
        result['total_pages'] = len(pdf.pages)

        page_range = pages if pages is not None else range(len(pdf.pages))

        for i in page_range:
            if 0 <= i < len(pdf.pages):
                page = pdf.pages[i]
                result['text'][i + 1] = page.extract_text() or ""
                # 提取表格
                tables = page.extract_tables()
                if tables:
                    result['tables'][i + 1] = tables

    return result

# 使用示例
pdf_path = "/Users/moonshot/Desktop/桌面整理/项目/pku大四下/逻辑导论/lectures/2.一只麻雀与逻辑学的起源.pdf"

content = read_pdf_pdfplumber(pdf_path, pages=[0, 1])

# 查看表格
if content['tables']:
    for page_num, tables in content['tables'].items():
        print(f"第 {page_num} 页有 {len(tables)} 个表格")
```

### 方法3: 提取图片

```python
import fitz
from PIL import Image
import io

def extract_images(pdf_path, page_num=0):
    """从PDF指定页提取图片"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    images = []
    for img_index, img in enumerate(page.get_images(), start=1):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        # 转换为PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        images.append({
            'ext': image_ext,
            'image': image,
            'bytes': image_bytes
        })

    doc.close()
    return images

# 使用示例
# images = extract_images(pdf_path, page_num=0)
# for img in images:
#     img['image'].save(f"image.{img['ext']}")
```

## 完整工具类

```python
import fitz
import pdfplumber
from pathlib import Path


class PDFReader:
    """PDF读取工具类，整合多种读取方式"""

    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    def get_info(self):
        """获取PDF基本信息"""
        with fitz.open(self.pdf_path) as doc:
            return {
                'pages': len(doc),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
            }

    def read_text(self, pages=None, mode='fast'):
        """
        读取文本

        Args:
            pages: 页码列表或None(全部)
            mode: 'fast'(PyMuPDF) 或 'table'(pdfplumber)
        """
        if mode == 'fast':
            return self._read_pymupdf(pages)
        else:
            return self._read_pdfplumber(pages)

    def _read_pymupdf(self, pages):
        """PyMuPDF快速读取"""
        doc = fitz.open(self.pdf_path)
        result = {}
        page_range = pages if pages is not None else range(len(doc))

        for i in page_range:
            if 0 <= i < len(doc):
                result[i + 1] = doc[i].get_text()

        doc.close()
        return result

    def _read_pdfplumber(self, pages):
        """pdfplumber读取（支持表格）"""
        result = {'text': {}, 'tables': {}}

        with pdfplumber.open(self.pdf_path) as pdf:
            page_range = pages if pages is not None else range(len(pdf.pages))

            for i in page_range:
                if 0 <= i < len(pdf.pages):
                    page = pdf.pages[i]
                    result['text'][i + 1] = page.extract_text() or ""
                    tables = page.extract_tables()
                    if tables:
                        result['tables'][i + 1] = tables

        return result

    def search(self, keyword):
        """搜索关键词，返回所在页码列表"""
        matches = []
        doc = fitz.open(self.pdf_path)

        for i, page in enumerate(doc):
            text = page.get_text()
            if keyword in text:
                matches.append(i + 1)

        doc.close()
        return matches


# 使用示例
# reader = PDFReader("path/to/file.pdf")
# info = reader.get_info()
# text = reader.read_text(pages=range(5))
# pages_with_keyword = reader.search("关键词")
```

## 方案对比

| 特性 | PyMuPDF | pdfplumber |
|------|---------|------------|
| 速度 | 极快 (~0.04s/76页) | 较快 (~1s/76页) |
| 中文支持 | 优秀 | 优秀 |
| 表格提取 | 一般 | 强大 |
| 图片提取 | 支持 | 不支持 |
| 内存占用 | 低 | 中等 |
| 推荐场景 | 快速阅读、搜索 | 数据分析、表格提取 |

## 扫描版 PDF：OCR 兜底

课件、往年题回忆版常是**扫描件**（图片型 PDF，没有文本层），上述所有方法都会返回空文本。流程不能在这里卡死——先判定，再走 OCR。

### 判定是否扫描件

```python
import fitz

def is_scanned(pdf_path, sample_pages=3):
    """前几页抽样：文本极少但有整页图片 → 判定为扫描件"""
    doc = fitz.open(pdf_path)
    n = min(sample_pages, doc.page_count)
    text_len = sum(len(doc[i].get_text().strip()) for i in range(n))
    has_images = any(doc[i].get_images() for i in range(n))
    doc.close()
    return text_len < 50 * n and has_images
```

### OCR 方案（pytesseract，改编自 Anthropic pdf skill，MIT）

依赖：`brew install tesseract tesseract-lang`（中文需 `chi_sim` 语言包，`tesseract-lang` 含之；Linux 用 `apt install tesseract-ocr tesseract-ocr-chi-sim`），Python 侧 `uv add pymupdf pytesseract pillow`。

```python
import io
import fitz
import pytesseract
from PIL import Image

def ocr_pdf(pdf_path, lang="chi_sim+eng", dpi=200, pages=None):
    """用 PyMuPDF 直接光栅化（无需 poppler），逐页 OCR"""
    doc = fitz.open(pdf_path)
    page_range = pages if pages is not None else range(doc.page_count)
    out = []
    for i in page_range:
        pix = doc[i].get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        out.append(pytesseract.image_to_string(img, lang=lang))
    doc.close()
    return "\n\n".join(out)

# 组合用法：先常规提取，空了再 OCR
# text = ocr_pdf(pdf_path) if is_scanned(pdf_path) else read_pdf_fast(pdf_path)
```

注意：

- OCR 结果的数学公式基本不可靠（上下标、希腊字母易错），扫描版课件里的公式以**人工核对**为前提使用，或在笔记流程中标注"来自 OCR，需核对"
- `dpi=200` 是速度/精度平衡点；公式密集页可提到 300
- `tesseract` 不存在时降级：报告用户该 PDF 为扫描件、需要安装 OCR 依赖，不要静默返回空文本

## 注意事项

1. **扫描版PDF**: 上述常规方法只能提取文本层，扫描版需走上一节的 OCR 兜底
2. **密码保护**: 需要先移除密码或使用 `fitz.open(password="xxx")`
3. **大文件**: 超过100MB的PDF建议分页读取，避免内存溢出
