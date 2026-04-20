import os
from PyQt6.QtWidgets import QLineEdit


class DropLineEdit(QLineEdit):
    """A QLineEdit that accepts drag-and-drop for directory paths."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and os.path.isdir(url.toLocalFile()):
                event.acceptProposedAction()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        self.setText(url.toLocalFile())
