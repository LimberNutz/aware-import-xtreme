import os
from pathlib import Path


def scan_folders(root_path, max_depth, folder_cache):
    cache_key = (str(root_path), max_depth)
    if cache_key in folder_cache:
        return folder_cache[cache_key]

    folders = []
    root = Path(root_path)

    if not root.exists():
        folder_cache[cache_key] = folders
        return folders

    for depth in range(max_depth + 1):
        pattern = "*"
        for _ in range(depth):
            pattern = os.path.join(pattern, "*")

        for folder_path in root.glob(pattern):
            if folder_path.is_dir() and folder_path != root:
                rel_path = folder_path.relative_to(root)
                folders.append({
                    'full_path': folder_path,
                    'relative_path': rel_path,
                    'name': folder_path.name,
                })

    folder_cache[cache_key] = folders
    return folders


def extract_pattern_from_filename(filename, folders):
    if not folders:
        return None

    sorted_folders = sorted(folders, key=lambda folder: len(folder['name']), reverse=True)
    for folder in sorted_folders:
        if folder['name'] in filename:
            return folder
    return None


def ext_folder(ext: str) -> str:
    if not ext:
        return "Unsorted"
    return ext.lstrip('.').upper()


def suggest_destination(file_info, destination_root, use_extension_mode, max_depth, folder_cache):
    root = Path(destination_root)
    filename = file_info.get('filename', '')

    if use_extension_mode or not filename:
        ext = file_info.get('extension', '')
        folder = ext_folder(ext)
        return root / folder / filename

    folders = scan_folders(destination_root, max_depth, folder_cache)
    matched_folder = extract_pattern_from_filename(filename, folders)
    if matched_folder:
        dest_path = matched_folder['full_path'] / filename
        return dest_path, matched_folder['name'], "Matched"
    return None, None, "Unmatched"
