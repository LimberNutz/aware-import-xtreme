import concurrent.futures
import datetime
import hashlib
import mimetypes
import os
import re
import time
from collections import defaultdict
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from constants import EXCLUDED_EXTENSIONS, LARGE_DIR_THRESHOLD, MAX_RESULTS, MAX_SCAN_FILES


class SearchEngine(QObject):
    """Core logic for finding files and duplicates. Can be used by GUI or CLI."""
    progress_update = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.stopped = False
        self.match_count = 0
        self.group_count = 0
        self.scan_start_time = None
        self.last_progress_time = 0
        self.last_processed_count = 0

    def stop(self):
        self.stopped = True

    def get_result_summary(self):
        return {'match_count': self.match_count, 'group_count': self.group_count}

    def _hash_file(self, path):
        """Calculate SHA256 hash of a file."""
        h = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(h.block_size * 1024)
                    if not chunk or self.stopped:
                        break
                    h.update(chunk)
            return h.hexdigest() if not self.stopped else None
        except (IOError, OSError):
            return None

    def find_duplicates(self, params):
        """Generator that finds and yields groups of duplicate files."""
        self.stopped = False
        self.match_count = 0
        self.group_count = 0

        self.progress_update.emit(0, "Stage 1/3: Grouping files by size...")
        size_map = defaultdict(list)
        total_files, processed_count = self._pre_scan(params)

        for root, dirs, files in os.walk(params['search_dir']):
            if self.stopped:
                return
            dirs[:] = [d for d in dirs if Path(root, d).as_posix() not in params['exclude_dirs']]
            for file in files:
                if self.stopped:
                    return
                processed_count += 1
                try:
                    path = Path(root, file)
                    size = path.stat().st_size
                    if size > params.get('min_size_bytes', 1024):
                        size_map[size].append(path)
                except OSError:
                    continue
                if total_files > 0:
                    self.progress_update.emit(int(processed_count / total_files * 33), f"Scanned {processed_count}/{total_files} files...")

        self.progress_update.emit(33, "Stage 2/3: Hashing potential duplicates...")
        hash_map = defaultdict(list)
        potential_dupes = {size: paths for size, paths in size_map.items() if len(paths) > 1}

        files_to_hash = sum(len(paths) for paths in potential_dupes.values())
        hashed_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_path = {executor.submit(self._hash_file, path): path for size, paths in potential_dupes.items() for path in paths}
            for future in concurrent.futures.as_completed(future_to_path):
                if self.stopped:
                    executor.shutdown(wait=False)
                    return
                path = future_to_path[future]
                try:
                    file_hash = future.result()
                    if file_hash:
                        hash_map[file_hash].append(path)
                except Exception:
                    pass
                hashed_count += 1
                if files_to_hash > 0:
                    self.progress_update.emit(33 + int(hashed_count / files_to_hash * 33), f"Hashed {hashed_count}/{files_to_hash} files...")

        self.progress_update.emit(66, "Stage 3/3: Finalizing groups...")
        duplicate_groups = {h: p for h, p in hash_map.items() if len(p) > 1}
        self.group_count = len(duplicate_groups)

        for file_hash, paths in duplicate_groups.items():
            if self.stopped:
                return
            file_group = []
            for path in paths:
                self.match_count += 1
                info = self._get_file_info(path, {'hash': file_hash})
                if info:
                    file_group.append(info)
            if file_group:
                yield file_group

    def find_files(self, params):
        """Generator that finds and yields files matching criteria with multi-threaded scanning."""
        self.stopped = False
        self.match_count = 0
        self._compile_patterns(params)
        total_files, processed_count = self._pre_scan(params)
        self.scan_start_time = time.time()
        self.last_progress_time = self.scan_start_time
        self.last_processed_count = 0

        if total_files > LARGE_DIR_THRESHOLD:
            self.progress_update.emit(0, f"⚠️ Large directory detected: {total_files:,} files. Scan limited to {MAX_RESULTS:,} results.")

        if params.get('use_multithreading', True):
            for file_info in self._find_files_multithreaded(params, total_files):
                if self.stopped:
                    break
                if self.match_count >= MAX_RESULTS:
                    self.progress_update.emit(100, f"⚠️ Reached maximum results limit ({MAX_RESULTS:,}). Use more specific search criteria.")
                    break
                yield file_info
        else:
            for file_info in self._find_files_singlethreaded(params, total_files, 0):
                if self.stopped:
                    break
                if self.match_count >= MAX_RESULTS:
                    self.progress_update.emit(100, f"⚠️ Reached maximum results limit ({MAX_RESULTS:,}). Use more specific search criteria.")
                    break
                yield file_info

    def _find_files_singlethreaded(self, params, total_files, processed_count):
        """Original single-threaded implementation"""
        for root, dirs, files in os.walk(params['search_dir']):
            if self.stopped:
                break
            dirs[:] = [d for d in dirs if Path(root, d).as_posix() not in params['exclude_dirs']]

            current_folder = Path(root).name or str(root)
            if len(current_folder) > 50:
                current_folder = '...' + current_folder[-47:]

            for file in files:
                if self.stopped:
                    break
                processed_count += 1

                if processed_count >= MAX_SCAN_FILES:
                    self.progress_update.emit(100, f"⚠️ Scan limit reached ({MAX_SCAN_FILES:,} files). Use more specific search criteria.")
                    break

                if total_files > 0 and processed_count % 100 == 0:
                    speed_info = self._calculate_speed(processed_count)
                    progress_msg = f"📂 {current_folder} | {processed_count:,}/{total_files:,} files{speed_info}"
                    self.progress_update.emit(int(processed_count / total_files * 100), progress_msg)
                elif total_files <= 0 and processed_count % 500 == 0:
                    speed_info = self._calculate_speed(processed_count)
                    progress_msg = f"📂 {current_folder} | {processed_count:,} files{speed_info}"
                    self.progress_update.emit(-1, progress_msg)

                file_path = Path(root, file)
                if self._is_file_match(file_path, params):
                    self.match_count += 1
                    info = self._get_file_info(file_path)
                    if info:
                        yield info

    def _find_files_multithreaded(self, params, total_files):
        """Multi-threaded implementation using ThreadPoolExecutor for parallel directory scanning"""
        import queue
        import threading

        result_queue = queue.Queue(maxsize=1000)
        processed_count = [0]
        counter_lock = threading.Lock()

        def scan_directory(dir_path):
            """Scan a single directory and its subdirectories"""
            local_results = []
            try:
                for root, dirs, files in os.walk(dir_path):
                    if self.stopped:
                        break

                    dirs[:] = [d for d in dirs if Path(root, d).as_posix() not in params['exclude_dirs']]

                    current_folder = Path(root).name or str(root)
                    if len(current_folder) > 50:
                        current_folder = '...' + current_folder[-47:]

                    for file in files:
                        if self.stopped:
                            break

                        with counter_lock:
                            processed_count[0] += 1
                            count = processed_count[0]

                        if count >= MAX_SCAN_FILES:
                            self.progress_update.emit(100, f"⚠️ Scan limit reached ({MAX_SCAN_FILES:,} files). Use more specific search criteria.")
                            break

                        if count % 200 == 0:
                            speed_info = self._calculate_speed(count)
                            if total_files > 0:
                                progress_msg = f"📂 {current_folder} | {count:,}/{total_files:,} files{speed_info}"
                                self.progress_update.emit(int(count / total_files * 100), progress_msg)
                            else:
                                progress_msg = f"📂 {current_folder} | {count:,} files{speed_info}"
                                self.progress_update.emit(-1, progress_msg)

                        file_path = Path(root, file)
                        if self._is_file_match(file_path, params):
                            info = self._get_file_info(file_path)
                            if info:
                                local_results.append(info)
                                if len(local_results) >= 50:
                                    result_queue.put(local_results.copy())
                                    local_results.clear()
            except Exception:
                pass

            if local_results:
                result_queue.put(local_results)

        search_dir = Path(params['search_dir'])
        subdirs = []
        try:
            for item in search_dir.iterdir():
                if item.is_dir() and item.as_posix() not in params['exclude_dirs']:
                    subdirs.append(str(item))
        except Exception:
            subdirs = [str(search_dir)]

        if len(subdirs) < 2:
            subdirs = [str(search_dir)]

        max_workers = min(os.cpu_count() or 4, len(subdirs), 8)

        def producer():
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(scan_directory, subdir) for subdir in subdirs]
                concurrent.futures.wait(futures)
            result_queue.put(None)

        producer_thread = threading.Thread(target=producer, daemon=True)
        producer_thread.start()

        while True:
            batch = result_queue.get()
            if batch is None:
                break
            for file_info in batch:
                self.match_count += 1
                yield file_info
                if self.stopped:
                    return

    def _pre_scan(self, params):
        if params.get('count_files', True):
            total_files = self._count_files(params)
            return total_files, 0
        return -1, 0

    def _count_files(self, params):
        self.progress_update.emit(0, "Counting total files...")
        count = 0
        for root, dirs, files in os.walk(params['search_dir']):
            if self.stopped:
                return -1
            dirs[:] = [d for d in dirs if Path(root, d).as_posix() not in params['exclude_dirs']]
            count += len(files)
        self.progress_update.emit(0, f"Found {count} total files to process.")
        return count

    def _get_file_info(self, file_path, extra_data=None):
        try:
            stat = file_path.stat()
            info = {
                'filename': file_path.name,
                'path': str(file_path.parent),
                'full_path': str(file_path),
                'extension': file_path.suffix.lower(),
                'size_kb': round(stat.st_size / 1024, 2),
                'size_bytes': stat.st_size,
                'modified_date': datetime.datetime.fromtimestamp(stat.st_mtime),
                'created_date': datetime.datetime.fromtimestamp(stat.st_ctime),
            }
            if extra_data:
                info.update(extra_data)
            return info
        except OSError:
            return None

    def _calculate_speed(self, processed_count):
        """Calculate and format scanning speed"""
        current_time = time.time()
        time_diff = current_time - self.last_progress_time

        if time_diff > 0.5:
            files_diff = processed_count - self.last_processed_count
            speed = files_diff / time_diff
            self.last_progress_time = current_time
            self.last_processed_count = processed_count

            elapsed = current_time - self.scan_start_time
            elapsed_str = f"{int(elapsed)}s"
            if elapsed >= 60:
                elapsed_str = f"{int(elapsed//60)}m {int(elapsed%60)}s"

            return f" | ⚡ {speed:.0f}/s | ⏱️ {elapsed_str}"
        return ""

    def _compile_patterns(self, params):
        self.keywords = [k.lower().strip() for k in params['keywords'].split(',') if k.strip()]
        self.exclusion_keywords = [k.lower().strip() for k in params['exclusion_keywords'].split(',') if k.strip()]
        if params['use_regex']:
            self.patterns = [re.compile(kw, re.IGNORECASE) for kw in self.keywords]
            self.exclusion_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.exclusion_keywords]
        elif params['whole_words']:
            self.patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in self.keywords]
            self.exclusion_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in self.exclusion_keywords]
        else:
            self.patterns = self.keywords
            self.exclusion_patterns = self.exclusion_keywords

    def _is_file_match(self, file_path, params):
        file_ext = file_path.suffix.lower()
        if not file_ext or file_ext in EXCLUDED_EXTENSIONS:
            return False
        if params['allowed_extensions'] and file_ext.lstrip('.') not in params['allowed_extensions']:
            return False
        try:
            file_size_kb = file_path.stat().st_size / 1024
            if params['min_size_kb'] is not None and file_size_kb < params['min_size_kb']:
                return False
            if params['max_size_kb'] is not None and file_size_kb > params['max_size_kb']:
                return False
        except OSError:
            return False
        if params['date_filter']:
            try:
                ts = file_path.stat().st_mtime if params['date_filter_type'] == 'modified' else file_path.stat().st_ctime
                file_date = datetime.datetime.fromtimestamp(ts)
                if params['min_date'] and file_date < params['min_date']:
                    return False
                if params['max_date'] and file_date > params['max_date']:
                    return False
            except OSError:
                return False
        if params.get('content_search'):
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and mime_type.startswith('text/'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024 * 1024)
                        if params['content_search'].lower() not in content.lower():
                            return False
                except Exception:
                    return False
        return self._matches_keywords(file_path.stem)

    def _matches_keywords(self, file_name):
        if not self.keywords and not self.exclusion_keywords:
            return True
        file_name_lower = file_name.lower()
        if self.exclusion_keywords:
            if self.exclusion_patterns and isinstance(self.exclusion_patterns[0], re.Pattern):
                if any(p.search(file_name_lower) for p in self.exclusion_patterns):
                    return False
            else:
                if any(kw in file_name_lower for kw in self.exclusion_patterns):
                    return False
        if not self.keywords:
            return True
        if self.patterns and isinstance(self.patterns[0], re.Pattern):
            return any(p.search(file_name_lower) for p in self.patterns)
        else:
            return any(kw in file_name_lower for kw in self.patterns)
