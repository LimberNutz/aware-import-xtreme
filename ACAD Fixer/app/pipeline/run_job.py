import logging
import os
import shutil
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.parsers.csv_parser import GGCSVParser, AssetRecord
from app.config import AppConfig
from app.pipeline.lookup import build_lookup, write_lookup_file
from app.cad.oda import ODAConverter
from app.cad.dxf_editor import DXFEditor
from app.pdf.pdf_editor import PDFEditor


class JobManager:
    """Orchestrates the title-block update pipeline."""

    def __init__(self, args):
        self.args = args
        config_path = getattr(args, "config", None)
        self.config = AppConfig.load(config_path)

    # -----------------------------------------------------------------
    # Commands
    # -----------------------------------------------------------------

    def run(self):
        logging.info("Starting Full Run...")
        record = self._get_record_for_asset(self.args.asset)
        if not record:
            logging.error(f"No record found for asset {self.args.asset}. Aborting.")
            return
        self._process_asset(record)

    def parse_only(self):
        record = self._get_record_for_asset(self.args.asset)
        if not record:
            return
        lookup = build_lookup(record)
        print(lookup)
        cad_root = Path(self.config.cad_root) if self.config.cad_root else Path(".")
        if cad_root.exists():
            write_lookup_file(lookup, cad_root, record.equipment_id)

    def validate_only(self):
        logging.info(f"Validating lookup: {self.args.lookup}")
        from app.pipeline.lookup import read_lookup_file
        data = read_lookup_file(Path(self.args.lookup))
        for k, v in data.items():
            logging.info(f"  {k}={v}")

    def probe_dxf(self, file_path):
        logging.info(f"Probing DXF: {file_path}")
        editor = DXFEditor(file_path)
        if not editor.load():
            return
        msp = editor.doc.modelspace()
        for ent in msp.query("INSERT"):
            if ent.has_attrib:
                for attr in ent.attribs:
                    logging.info(f"  ATTRIB[{attr.dxf.tag}]='{attr.dxf.text}'")

    def probe_pdf(self, file_path):
        logging.info(f"Probing PDF: {file_path}")
        editor = PDFEditor(file_path)
        if not editor.load():
            return
        for i, page in enumerate(editor.doc):
            logging.info(f"  Page {i+1} rotation={page.rotation}")
            for span in editor._collect_spans(page):
                logging.info(f"    '{span['text']}' @ {span['bbox']}")

    def batch_run(self):
        logging.info("Starting Batch Run...")
        assets = self._get_all_assets()
        if not assets:
            logging.error("No assets found in CSV. Aborting.")
            return
        exclusions = [x.strip() for x in (self.args.exclude or "").split(",") if x.strip()]
        logging.info(f"Total assets: {len(assets)}, Excluding: {len(exclusions)}")

        processed = skipped = failed = 0
        for asset_id in assets:
            if asset_id in exclusions:
                logging.info(f"Skipping excluded asset: {asset_id}")
                skipped += 1
                continue
            logging.info(f"=== Processing asset: {asset_id} ===")
            record = self._get_record_for_asset(asset_id)
            if not record:
                logging.warning(f"No record for {asset_id}")
                failed += 1
                continue
            try:
                ok = self._process_asset(record)
                if ok:
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                logging.exception(f"Asset {asset_id} failed: {e}")
                failed += 1
        logging.info(f"Batch complete. Processed: {processed}, Skipped: {skipped}, Failed: {failed}")

    # -----------------------------------------------------------------
    # Per-asset processing
    # -----------------------------------------------------------------

    def _process_asset(self, record: AssetRecord) -> bool:
        asset_id = record.equipment_id
        lookup = build_lookup(record)
        logging.info(f"Derived Lookup for {asset_id}: {lookup}")

        cad_root = Path(self.config.cad_root) if self.config.cad_root else Path(".")
        if cad_root.exists():
            write_lookup_file(lookup, cad_root, asset_id)

        if getattr(self.args, "dry_run", False):
            logging.info(f"DRY RUN: No files will be modified for {asset_id}.")
            return True

        # Validate config for actual run
        errors = self.config.validate_for_run()
        if errors:
            for e in errors:
                logging.error(f"Config error: {e}")
            return False

        # Locate source DWGs and PDFs for this asset in cad_root
        dwg_sources = self._find_files(cad_root, asset_id, ".dwg")
        pdf_sources = self._find_files(cad_root, asset_id, ".pdf")
        logging.info(f"Found {len(dwg_sources)} DWG(s) and {len(pdf_sources)} PDF(s) for {asset_id}")

        if not dwg_sources and not pdf_sources:
            logging.warning(f"No DWG/PDF files found for {asset_id} in {cad_root}")
            return False

        # Work directories
        work_dir = Path(self.config.work_root) / f"{asset_id}_auto"
        dwg_orig = work_dir / "dwg_orig"
        dwg_backup = work_dir / "dwg_backup"
        dxf_dir = work_dir / "dxf"
        dxf_edit = work_dir / "dxf_edited"
        dwg_out = work_dir / "dwg_updated"
        pdf_out = work_dir / "pdf_updated"
        log_dir = work_dir / "logs"
        for d in (dwg_orig, dwg_backup, dxf_dir, dxf_edit, dwg_out, pdf_out, log_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Rules
        attrib_exact, overwrite, fill_blanks, text_replace = self._build_dwg_rules(lookup)
        pdf_replacements, pdf_exact = self._build_pdf_rules(lookup)

        summary: List[str] = []

        # DWG pipeline
        if dwg_sources:
            # Copy sources -> dwg_orig, backup originals
            for src in dwg_sources:
                shutil.copy2(src, dwg_orig / src.name)
                shutil.copy2(src, dwg_backup / src.name)

            oda = ODAConverter(self.config.oda_exe, log_dir=str(log_dir))

            # DWG -> DXF
            if not oda.dwg_to_dxf(str(dwg_orig), str(dxf_dir), version=self.config.oda_version):
                logging.error("ODA DWG->DXF failed. Aborting DWG pipeline.")
            else:
                # Edit each DXF
                for dxf in sorted(dxf_dir.glob("*.dxf")):
                    editor = DXFEditor(str(dxf))
                    if not editor.load():
                        continue
                    n = editor.apply(
                        attrib_exact=attrib_exact,
                        overwrite=overwrite,
                        fill_blanks=fill_blanks,
                        text_replace=text_replace,
                    )
                    out_path = dxf_edit / dxf.name
                    editor.save(str(out_path))
                    summary.append(f"{dxf.name}: {n} DXF edits")
                    for ch in editor.changes:
                        summary.append(f"  - {ch}")

                # DXF -> DWG
                if not oda.dxf_to_dwg(str(dxf_edit), str(dwg_out), version=self.config.oda_version):
                    logging.error("ODA DXF->DWG failed. Updated DWGs not produced.")
                else:
                    # Copy updated DWGs back to cad_root (originals preserved in dwg_backup)
                    for updated in sorted(dwg_out.glob("*.dwg")):
                        dest = cad_root / updated.name
                        shutil.copy2(updated, dest)
                        summary.append(f"Updated: {dest}")

        # PDF pipeline
        for pdf_src in pdf_sources:
            editor = PDFEditor(str(pdf_src), rotation=self.config.pdf_rotation)
            if not editor.load():
                continue
            n = editor.apply(replacements=pdf_replacements, exact=pdf_exact)
            out_path = pdf_out / pdf_src.name
            editor.save(str(out_path))
            # Backup original then overwrite in cad_root
            backup = dwg_backup / pdf_src.name
            if not backup.exists():
                shutil.copy2(pdf_src, backup)
            shutil.copy2(out_path, pdf_src)
            summary.append(f"{pdf_src.name}: {n} PDF edits")
            for ch in editor.changes:
                summary.append(f"  - {ch}")

        # Write summary
        summary_path = work_dir / f"{asset_id}_summary.txt"
        with open(summary_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(summary) + "\n")
        logging.info(f"Summary: {summary_path}")
        for line in summary:
            logging.info(line)
        return True

    # -----------------------------------------------------------------
    # Rule builders
    # -----------------------------------------------------------------

    # Sentinels: lookup values we should NOT write to the drawing
    _SKIP_VALUES = {"", "Unknown"}

    def _build_dwg_rules(self, lookup: Dict[str, str]):
        """Build (ATTRIB_EXACT, OVERWRITE, FILL_BLANKS, TEXT_REPLACE) from lookup.

        Policy: CSV is the source of truth.
          - OVERWRITE all CSV-derived fields when CSV value is non-empty and
            differs from the current DWG value.
          - FILL_BLANKS only for YEAR_BLT (immutable once set; only fill if missing).
          - ATTRIB_EXACT retained for MATERIAL 'SS' -> 'C/SS' corruption guard.
        """
        attrib_exact: Dict[str, Tuple[str, str]] = {}
        overwrite: Dict[str, str] = {}
        fill_blanks: Dict[str, str] = {}

        # MATERIAL: 'Unknown' sentinel means "don't touch the drawing"
        material = lookup.get("MATERIAL", "")
        if material and material not in self._SKIP_VALUES:
            # SS->C/SS exact-value guard fires first; if the existing value is exactly 'SS'
            # and CSV says 'C/SS', we want the exact guard (equivalent to overwrite here).
            if material == "C/SS":
                attrib_exact["MATERIAL"] = ("SS", "C/SS")
            overwrite["MATERIAL"] = material

        # YEAR_BLT: only fill when blank (don't overwrite an existing year)
        year = lookup.get("YEAR_BLT", "")
        if year:
            fill_blanks["YEAR_BLT"] = year

        # All other CSV-derived fields: overwrite when CSV value is present
        for tag in (
            "CLASS", "B31_TYPE", "PID_NUMBER", "OD_IN",
            "PRESSURE", "TEMPERATURE",
            "CIRCUIT_DESC1", "CIRCUIT_DESC2",
        ):
            val = lookup.get(tag, "")
            if val and val not in self._SKIP_VALUES:
                overwrite[tag] = val

        # Do NOT put 'SS' -> 'C/SS' here (would corrupt PROCESS, CLASS labels)
        text_replace: List[Tuple[str, str]] = []
        return attrib_exact, overwrite, fill_blanks, text_replace

    def _build_pdf_rules(self, lookup: Dict[str, str]):
        """Build PDF substring + exact replacements."""
        replacements: Dict[str, str] = {}
        exact: Dict[str, str] = {}
        # Use exact matches to avoid corrupting labels
        if lookup.get("MATERIAL"):
            exact["SS"] = lookup["MATERIAL"]  # only spans whose whole text == "SS"
        if lookup.get("TEMPERATURE_PDF"):
            # Temperature: replace any '500\u00B0' style tokens? Keep simple via exact blank fills
            pass
        return replacements, exact

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _get_record_for_asset(self, asset_id: str) -> Optional[AssetRecord]:
        csv_path = getattr(self.args, "csv", None) or self.config.default_csv
        if not csv_path:
            logging.error("No CSV path provided (--csv or config.default_csv)")
            return None
        return GGCSVParser(csv_path, asset_id).parse()

    def _get_all_assets(self) -> List[str]:
        csv_path = getattr(self.args, "csv", None) or self.config.default_csv
        if not csv_path:
            logging.error("No CSV path provided")
            return []
        try:
            with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                assets = set()
                for row in reader:
                    eid = (row.get("Equipment ID") or "").strip()
                    if eid:
                        assets.add(eid)
                return sorted(assets)
        except Exception as e:
            logging.error(f"Failed to read CSV for asset list: {e}")
            return []

    def _find_files(self, root: Path, asset_id: str, ext: str) -> List[Path]:
        ext = ext.lower()
        results: List[Path] = []
        for p in root.rglob(f"*{ext}"):
            if asset_id.upper() in p.name.upper():
                results.append(p)
        return sorted(results)
