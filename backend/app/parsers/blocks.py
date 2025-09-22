from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from docx.document import Document as DocxDocument
from docx.text.paragraph import Paragraph


@dataclass
class Block:
    kind: str  # 'heading' | 'bullet' | 'paragraph' | 'table'
    level: int | None
    lines: List[str]

    def text(self) -> str:
        return "\n".join([ln for ln in self.lines if ln])


def _is_heading(p: Paragraph) -> Tuple[bool, int | None]:
    try:
        style_name = (p.style.name or "").lower()
    except Exception:
        style_name = ""
    if style_name.startswith("heading"):
        # e.g., "Heading 1"
        try:
            parts = style_name.split()
            lvl = int(parts[-1]) if parts and parts[-1].isdigit() else 1
        except Exception:
            lvl = 1
        return True, lvl
    # Some documents use Title as top heading
    if style_name == "title":
        return True, 1
    return False, None


def _is_bullet_or_numbered(p: Paragraph) -> bool:
    # Detect via numbering properties or style name hints
    try:
        if p._p is not None and p._p.pPr is not None and p._p.pPr.numPr is not None:  # type: ignore[attr-defined]
            return True
    except Exception:
        pass
    try:
        style_name = (p.style.name or "").lower()
        if any(tok in style_name for tok in ["bullet", "list", "number"]):
            return True
    except Exception:
        pass
    return False


def extract_blocks(doc: DocxDocument) -> List[Block]:
    blocks: List[Block] = []

    # Pass 1: paragraphs
    current_para_lines: List[str] = []
    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if not text:
            continue
        is_head, level = _is_heading(p)
        if is_head:
            # flush paragraph buffer
            if current_para_lines:
                blocks.append(Block(kind="paragraph", level=None, lines=current_para_lines))
                current_para_lines = []
            blocks.append(Block(kind="heading", level=level, lines=[text]))
            continue
        if _is_bullet_or_numbered(p):
            # flush paragraph buffer
            if current_para_lines:
                blocks.append(Block(kind="paragraph", level=None, lines=current_para_lines))
                current_para_lines = []
            blocks.append(Block(kind="bullet", level=None, lines=[text]))
            continue
        # default paragraph aggregation
        current_para_lines.append(text)

    if current_para_lines:
        blocks.append(Block(kind="paragraph", level=None, lines=current_para_lines))

    # Note: Temporarily ignore table content per product request.

    return blocks


def build_full_text_and_slices(blocks: List[Block]) -> Tuple[str, List[int], List[int]]:
    """
    Return a tuple of:
      - full_text: concatenation of all block lines separated by \n
      - heading_starts: offsets in full_text where a heading line begins

      - candidate_slice_starts: offsets that are reasonable slice boundaries
        (includes heading starts, bullet starts, and table row starts)
    """
    pieces: List[str] = []
    heading_starts: List[int] = []
    slice_starts: List[int] = []

    offset = 0
    for b in blocks:
        if b.kind == "heading":
            for i, ln in enumerate(b.lines):
                if i == 0:
                    heading_starts.append(offset)
                slice_starts.append(offset)
                pieces.append(ln)
                offset += len(ln) + 1  # account for trailing \n when we join
        elif b.kind == "bullet":
            for ln in b.lines:
                slice_starts.append(offset)
                pieces.append(ln)
                offset += len(ln) + 1
        elif b.kind == "paragraph":
            # keep paragraph lines but do not mark each line as a slice; only the start
            first_in_para = True
            for ln in b.lines:
                if first_in_para:
                    slice_starts.append(offset)
                    first_in_para = False
                pieces.append(ln)
                offset += len(ln) + 1
        elif b.kind == "table":
            for ln in b.lines:
                slice_starts.append(offset)
                pieces.append(ln)
                offset += len(ln) + 1

    full_text = "\n".join(pieces)
    return full_text, heading_starts, slice_starts
