import fitz  # PyMuPDF
import logging
from typing import Dict, List, Tuple, Optional


class PDFEditor:
    """Edits PDF title blocks via redact + re-insert.

    GG drawings are typically rotated 270 degrees (text flows vertically).
    Replacement flow:
      1. Find text span rects via search_for / rawdict
      2. Redact span (white fill)
      3. Insert new text at same position, preserving font size
    """

    def __init__(self, file_path: str, rotation: int = 270):
        self.file_path = file_path
        self.doc = None
        self.rotation = rotation
        self.changes: List[str] = []

    def load(self) -> bool:
        try:
            self.doc = fitz.open(self.file_path)
            return True
        except Exception as e:
            logging.error(f"Failed to load PDF {self.file_path}: {e}")
            return False

    def apply(
        self,
        replacements: Dict[str, str],
        exact: Optional[Dict[str, str]] = None,
    ) -> int:
        """Apply substring replacements.

        - replacements: {old_text: new_text} substring replacements on any matching span
        - exact: {old_text: new_text} only replaces when span text equals old_text
        """
        if not self.doc:
            return 0
        exact = exact or {}

        for page in self.doc:
            # Collect span info before mutating
            spans = self._collect_spans(page)
            # Gather edits per span
            edits: List[Tuple[fitz.Rect, str, float, str]] = []
            for span in spans:
                text = span["text"]
                rect = fitz.Rect(span["bbox"])
                fontsize = span.get("size", 8)
                new_text = None
                if text in exact:
                    new_text = exact[text]
                else:
                    out = text
                    for old, new in replacements.items():
                        if old and old in out:
                            out = out.replace(old, new)
                    if out != text:
                        new_text = out
                if new_text is not None:
                    edits.append((rect, new_text, fontsize, text))

            if not edits:
                continue

            # Redact all targeted rects
            for rect, _new, _fs, _old in edits:
                page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

            # Re-insert new text
            for rect, new_text, fontsize, old in edits:
                self._insert_rotated(page, rect, new_text, fontsize)
                self.changes.append(f"PDF: '{old}' -> '{new_text}'")

        return len(self.changes)

    def _collect_spans(self, page) -> List[dict]:
        spans = []
        try:
            data = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        except Exception:
            data = page.get_text("dict")
        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text")
                    if not text:
                        # rawdict uses 'chars'
                        chars = span.get("chars", [])
                        text = "".join(c.get("c", "") for c in chars)
                        if text and "bbox" not in span and chars:
                            # Build bbox from chars
                            xs0 = [c["bbox"][0] for c in chars]
                            ys0 = [c["bbox"][1] for c in chars]
                            xs1 = [c["bbox"][2] for c in chars]
                            ys1 = [c["bbox"][3] for c in chars]
                            span = dict(span)
                            span["bbox"] = (min(xs0), min(ys0), max(xs1), max(ys1))
                    if not text:
                        continue
                    spans.append({
                        "text": text,
                        "bbox": span.get("bbox"),
                        "size": span.get("size", 8),
                    })
        return spans

    def _insert_rotated(self, page, rect: "fitz.Rect", text: str, fontsize: float):
        # For 270deg rotated GG drawings, insert text with rotate=270 at rect's bottom-left.
        try:
            if self.rotation == 270:
                # bottom-left-ish anchor, small vertical nudge
                point = fitz.Point(rect.x0, rect.y1)
                page.insert_text(
                    point, text,
                    fontsize=fontsize, rotate=270,
                    color=(0, 0, 0), fontname="helv",
                )
            else:
                point = fitz.Point(rect.x0, rect.y1 - 2)
                page.insert_text(
                    point, text,
                    fontsize=fontsize, rotate=self.rotation,
                    color=(0, 0, 0), fontname="helv",
                )
        except Exception as e:
            logging.warning(f"PDF insert_text failed for '{text}': {e}")

    def save(self, output_path: str) -> None:
        if self.doc:
            self.doc.save(output_path, garbage=3, deflate=True)
            logging.info(f"Saved PDF to: {output_path} ({len(self.changes)} changes)")

    # Back-compat API
    def update_text(self, replacements: Dict[str, str]) -> int:
        return self.apply(replacements=replacements)
