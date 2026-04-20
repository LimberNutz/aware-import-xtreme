from features.smart_sort.pattern_matcher import scan_folders


def find_best_fuzzy_folder(filename, folders):
    if not folders:
        return None

    best_match = None
    best_score = 0
    filename_lower = filename.lower()

    for folder in folders:
        score = 0
        folder_name = folder['name'].lower()

        for i in range(2, min(len(folder_name), 8)):
            if folder_name[:i] in filename_lower:
                score += i

        words = folder_name.split('-')
        for word in words:
            if word in filename_lower:
                score += len(word) * 2

        if score > best_score and score > 3:
            best_score = score
            best_match = folder

    return best_match


def fuzzy_match_folder(filename, destination_root, max_depth, folder_cache):
    folders = scan_folders(destination_root, max_depth, folder_cache)
    return find_best_fuzzy_folder(filename, folders)
