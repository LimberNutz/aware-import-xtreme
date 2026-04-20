import re
import shutil
import tempfile
import os
from contextlib import contextmanager


@contextmanager
def temp_open_workbook(file_path: str, **kwargs):
    """Open an Excel file via a temporary copy so the original is never locked.

    Usage:
        with temp_open_workbook(path, data_only=True, read_only=True) as wb:
            sheet = wb.active
            ...
    The temp copy is deleted automatically when the block exits.
    """
    import openpyxl

    suffix = os.path.splitext(file_path)[1]  # .xlsx / .xlsm
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # close the raw file descriptor; shutil will write to the path
    try:
        shutil.copy2(file_path, tmp_path)
        wb = openpyxl.load_workbook(tmp_path, **kwargs)
        try:
            yield wb
        finally:
            wb.close()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def format_cml_standard(cml_raw: str) -> str:
    # format CML to standard style: 1.01, 1.02, 2.01
    cml_raw = str(cml_raw).strip()
    if not cml_raw:
        return cml_raw
    match = re.match(r"^(\d+)\.(\d+)$", cml_raw)
    if match:
        major = match.group(1)
        minor = match.group(2)
        return f"{major}.{minor.zfill(2)}"
    # try integer-only (e.g. "1" -> "1.01" doesn't make sense, keep as-is)
    return cml_raw


def format_cml_client(cml_raw: str) -> str:
    # format CML to client style: 1.1, 1.2 (strip trailing/leading zeros)
    cml_raw = str(cml_raw).strip()
    if not cml_raw:
        return cml_raw
    match = re.match(r"^(\d+)\.(\d+)$", cml_raw)
    if match:
        major = match.group(1)
        minor = str(int(match.group(2)))  # strip leading zeros
        return f"{major}.{minor}"
    return cml_raw


def cml_suffix_value(cml: str) -> int:
    # extract the numeric suffix from a CML like "1.06" -> 6
    match = re.match(r"^\d+\.(\d+)$", str(cml).strip())
    if match:
        return int(match.group(1))
    return 0


def safe_str(value) -> str:
    # convert cell value to clean string
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() == "none":
        return ""
    return s


def is_numeric(value: str) -> bool:
    # check if a string is a valid number
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def extract_system_name_from_filename(filename: str) -> str:
    # try to extract a system name token like "REFG-010" from filename
    # look for patterns like XXXX-NNN
    match = re.search(r"([A-Z]{2,}[\-_]?\d{2,})", filename.upper())
    if match:
        return match.group(1)
    # fallback: use filename without extension
    name = re.sub(r"\.(xlsx|xlsm)$", "", filename, flags=re.IGNORECASE)
    return name.strip()
