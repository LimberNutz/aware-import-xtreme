import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal


class ProcessManager(QObject):
    status_changed = Signal(str, str)   # tool_id, "running" | "stopped" | "crashed"
    log_message    = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._procs: dict[str, subprocess.Popen] = {}
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(500)

    def launch(self, tool_id: str, cmd: list[str], cwd: str) -> None:
        if self.is_running(tool_id):
            return
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.Popen(cmd, cwd=cwd, creationflags=flags)
            self._procs[tool_id] = proc
            self._emit_log(f"{tool_id} launched  (PID {proc.pid})")
            self.status_changed.emit(tool_id, "running")
        except Exception as exc:
            self._emit_log(f"{tool_id} failed to launch: {exc}")
            self.status_changed.emit(tool_id, "crashed")

    def stop(self, tool_id: str) -> None:
        proc = self._procs.get(tool_id)
        if proc and proc.poll() is None:
            proc.terminate()
            self._emit_log(f"{tool_id} stop requested")

    def is_running(self, tool_id: str) -> bool:
        proc = self._procs.get(tool_id)
        return proc is not None and proc.poll() is None

    def _poll(self) -> None:
        for tid, proc in list(self._procs.items()):
            if proc.poll() is not None:
                code = proc.returncode
                del self._procs[tid]
                status = "stopped" if code == 0 else "crashed"
                self._emit_log(f"{tid} exited  (code {code})")
                self.status_changed.emit(tid, status)

    def _emit_log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{ts}]  {msg}")
