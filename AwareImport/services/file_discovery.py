import os
import re
from typing import Optional
from app.constants import SUPPORTED_EXTENSIONS


def _parse_name_filters(name_filter: str) -> list[str]:
    return [term.strip().lower() for term in name_filter.split(",") if term.strip()]


def _matches_name_filters(filename: str, name_filters: list[str]) -> bool:
    if not name_filters:
        return True
    filename_lower = filename.lower()
    return any(term in filename_lower for term in name_filters)


def _exact_word_match(keyword: str, filename: str) -> bool:
    """Check if keyword matches as a whole word in filename."""
    # Create a regex pattern that matches the keyword as a whole word
    # \b matches word boundaries, and we escape the keyword to handle special regex chars
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    return bool(re.search(pattern, filename.lower(), flags=re.IGNORECASE))


def find_excel_files(root_folder: str) -> list[str]:
    # recursively find all supported Excel files in a folder
    results = []
    if not os.path.isdir(root_folder):
        return results
    for dirpath, _dirnames, filenames in os.walk(root_folder):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                # skip temp files
                if fname.startswith("~$"):
                    continue
                results.append(os.path.join(dirpath, fname))
    return sorted(results)


def fuzzy_match_files(
    entity_names: list[str],
    root_folder: str,
    threshold: int = 60,
) -> list[tuple[str, str, int]]:
    # match entity names to filenames using fuzzy matching
    # returns list of (entity_name, matched_file_path, score)
    try:
        from thefuzz import fuzz
    except ImportError:
        return [(name, "", 0) for name in entity_names]

    candidates = find_excel_files(root_folder)
    candidate_names = {
        os.path.splitext(os.path.basename(f))[0]: f for f in candidates
    }

    results = []
    for entity in entity_names:
        entity = entity.strip()
        if not entity:
            continue
        best_match = ""
        best_score = 0
        for cand_name, cand_path in candidate_names.items():
            score = fuzz.token_sort_ratio(entity.lower(), cand_name.lower())
            if score > best_score:
                best_score = score
                best_match = cand_path
        if best_score >= threshold:
            results.append((entity, best_match, best_score))
        else:
            results.append((entity, "", best_score))

    return results


def batch_search_files(
    keywords: list[str],
    root_folder: str,
    name_filter: str = "",
    exact_match: bool = False,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Search for files matching any of the given keywords (case-insensitive substring on filename).

    Args:
        keywords: Entity names to search for.
        root_folder: Root directory to search recursively.
        name_filter: If non-empty, filename must ALSO contain this term (e.g. 'UT').
        exact_match: If True, match whole words only (e.g. 'DR' won't match 'Drain').

    Returns:
        (matches, unmatched) where matches is a list of (matched_keyword, file_path)
        and unmatched is a list of keywords that had no hits.
    """
    candidates = find_excel_files(root_folder)
    name_filters = _parse_name_filters(name_filter)
    matches: list[tuple[str, str]] = []
    matched_keywords: set[str] = set()
    seen_paths: set[str] = set()

    for kw in keywords:
        kw_clean = kw.strip()
        if not kw_clean:
            continue
        kw_lower = kw_clean.lower()
        for fpath in candidates:
            fname = os.path.splitext(os.path.basename(fpath))[0].lower()

            # Use exact word match or substring match based on parameter
            keyword_matches = _exact_word_match(kw_clean, fname) if exact_match else kw_lower in fname

            if keyword_matches and fpath not in seen_paths:
                if not _matches_name_filters(fname, name_filters):
                    continue
                matches.append((kw_clean, fpath))
                seen_paths.add(fpath)
                matched_keywords.add(kw_clean)

    unmatched = [kw.strip() for kw in keywords if kw.strip() and kw.strip() not in matched_keywords]
    return matches, unmatched


def search_files_by_keyword(
    keyword: str,
    root_folder: str,
    search_content: bool = False,
    name_filter: str = "",
    exact_match: bool = False,
) -> list[str]:
    # search for keyword in filenames and optionally inside Excel content
    keyword_lower = keyword.lower()
    name_filters = _parse_name_filters(name_filter)
    matches = []

    candidates = find_excel_files(root_folder)
    for fpath in candidates:
        fname = os.path.basename(fpath).lower()
        # Apply filename filter if provided
        if not _matches_name_filters(fname, name_filters):
            continue

        # Use exact word match or substring match based on parameter
        keyword_matches = _exact_word_match(keyword, fname) if exact_match else keyword_lower in fname

        if keyword_matches:
            matches.append(fpath)
            continue

        if search_content:
            try:
                from utils.helpers import temp_open_workbook
                with temp_open_workbook(fpath, data_only=True, read_only=True) as wb:
                    found = False
                    for sheet_name in wb.sheetnames:
                        if found:
                            break
                        sheet = wb[sheet_name]
                        for row in sheet.iter_rows(max_row=20, values_only=True):
                            for cell in row:
                                if cell and keyword_lower in str(cell).lower():
                                    matches.append(fpath)
                                    found = True
                                    break
                            if found:
                                break
            except Exception:
                pass

    return matches
