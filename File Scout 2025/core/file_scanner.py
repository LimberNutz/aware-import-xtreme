from PyQt6.QtCore import QThread, pyqtSignal

from core.search_engine import SearchEngine


class FileSearchWorker(QThread):
    """Worker thread that runs the core search logic and emits signals."""
    progress_update = pyqtSignal(int, str)
    search_complete = pyqtSignal(bool, str)
    live_result = pyqtSignal(dict)
    duplicate_group_found = pyqtSignal(list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.engine = SearchEngine()
        self.engine.progress_update.connect(self.progress_update)
        self.stopped = False

    def run(self):
        try:
            if self.params['search_mode'] == 'duplicates':
                for group in self.engine.find_duplicates(self.params):
                    if self.stopped:
                        break
                    self.duplicate_group_found.emit(group)
            else:
                for file_info in self.engine.find_files(self.params):
                    if self.stopped:
                        break
                    self.live_result.emit(file_info)

            if self.stopped:
                self.search_complete.emit(False, "Search stopped by user.")
            else:
                summary = self.engine.get_result_summary()
                msg = f"Search complete. Found {summary['match_count']} files."
                if self.params['search_mode'] == 'duplicates':
                    msg = f"Search complete. Found {summary['match_count']} duplicate files in {summary['group_count']} groups."
                self.search_complete.emit(True, msg)
        except Exception as e:
            self.search_complete.emit(False, f"An error occurred: {e}")

    def stop(self):
        self.stopped = True
        self.engine.stop()
