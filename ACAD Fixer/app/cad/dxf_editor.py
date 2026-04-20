import ezdxf
from ezdxf import recover
import logging
from typing import Dict, List, Tuple, Optional


class DXFEditor:
    """Edits a DXF file using three rule sets:

    - ATTRIB_EXACT: {tag: (expected_value, new_value)} - only replaces when attrib value
      matches expected exactly (prevents e.g. 'PROCESS' -> 'PROCEC/SS' corruption).
    - FILL_BLANKS: {tag: new_value} - only fills when attrib value is blank.
    - TEXT_REPLACE: [(old, new), ...] substring replacements applied to TEXT/MTEXT
      entities (and to ATTRIB values when value != expected). Do NOT include 'SS'
      -> 'C/SS' here; use ATTRIB_EXACT for MATERIAL instead.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = None
        self.changes: List[str] = []

    def load(self) -> bool:
        try:
            self.doc, audit = recover.readfile(self.file_path)
            if audit.has_errors:
                logging.warning(f"DXF recovered with {len(audit.errors)} errors: {self.file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to load DXF {self.file_path}: {e}")
            return False

    def apply(
        self,
        attrib_exact: Optional[Dict[str, Tuple[str, str]]] = None,
        fill_blanks: Optional[Dict[str, str]] = None,
        overwrite: Optional[Dict[str, str]] = None,
        text_replace: Optional[List[Tuple[str, str]]] = None,
    ) -> int:
        """Apply all rules. Returns count of changes.

        Rule priority (per attrib): ATTRIB_EXACT > OVERWRITE > FILL_BLANKS > TEXT_REPLACE.
        - overwrite: always sets the attrib value when its current value differs
          (CSV is source of truth). Empty/sentinel values should be filtered out by caller.
        """
        if not self.doc:
            return 0
        attrib_exact = {k.upper(): v for k, v in (attrib_exact or {}).items()}
        fill_blanks = {k.upper(): v for k, v in (fill_blanks or {}).items()}
        overwrite = {k.upper(): v for k, v in (overwrite or {}).items()}
        text_replace = text_replace or []

        def patch_entity(ent):
            et = ent.dxftype()
            if et in ("TEXT", "MTEXT"):
                self._patch_text(ent, text_replace)
            elif et == "ATTRIB":
                self._patch_attrib(ent, attrib_exact, fill_blanks, overwrite, text_replace)
            elif et == "INSERT":
                # Iterate block reference attributes
                if ent.has_attrib:
                    for attr in ent.attribs:
                        self._patch_attrib(attr, attrib_exact, fill_blanks, overwrite, text_replace)

        # All layouts (modelspace + paperspace)
        for layout in self.doc.layouts:
            for ent in layout:
                patch_entity(ent)

        # Blocks (except anonymous)
        for block in self.doc.blocks:
            if block.name.startswith("*"):
                continue
            for ent in block:
                patch_entity(ent)

        return len(self.changes)

    def _patch_text(self, ent, text_replace):
        try:
            if ent.dxftype() == "MTEXT":
                old = ent.text
                new = old
                for a, b in text_replace:
                    if a and a in new:
                        new = new.replace(a, b)
                if new != old:
                    ent.text = new
                    self.changes.append(f"MTEXT: '{old}' -> '{new}'")
            else:
                old = ent.dxf.text
                new = old
                for a, b in text_replace:
                    if a and a in new:
                        new = new.replace(a, b)
                if new != old:
                    ent.dxf.text = new
                    self.changes.append(f"TEXT: '{old}' -> '{new}'")
        except Exception as e:
            logging.debug(f"Skipped text entity: {e}")

    def _patch_attrib(self, attr, attrib_exact, fill_blanks, overwrite, text_replace):
        try:
            tag = attr.dxf.tag.upper()
            old = attr.dxf.text or ""
            new = old

            # 1) Exact-value override (highest priority; special cases like SS->C/SS)
            if tag in attrib_exact:
                expected, replacement = attrib_exact[tag]
                if old.strip() == expected:
                    new = replacement

            # 2) Overwrite (CSV is source of truth; always replace when current != target)
            if new == old and tag in overwrite:
                target = overwrite[tag]
                if target and old.strip() != target.strip():
                    new = target

            # 3) Blank fill
            if new == old and tag in fill_blanks and not old.strip():
                new = fill_blanks[tag]

            # 4) Substring replacements (only if no higher-priority rule fired)
            if new == old:
                for a, b in text_replace:
                    if a and a in new:
                        new = new.replace(a, b)

            if new != old:
                attr.dxf.text = new
                self.changes.append(f"ATTRIB[{tag}]: '{old}' -> '{new}'")
        except Exception as e:
            logging.debug(f"Skipped attrib: {e}")

    def save(self, output_path: str) -> None:
        if self.doc:
            self.doc.saveas(output_path)
            logging.info(f"Saved DXF to: {output_path} ({len(self.changes)} changes)")

    def update_attributes(self, mapping: Dict[str, str]) -> int:
        """Back-compat: treat mapping as FILL_BLANKS."""
        return self.apply(fill_blanks=mapping)
