from constants import PreviewResult
from features.preview.handlers import (
    TextPreviewHandler,
    CodePreviewHandler,
    PDFPreviewHandler,
    ExcelPreviewHandler,
    CSVPreviewHandler,
    WordPreviewHandler,
    PowerPointPreviewHandler,
    AudioPreviewHandler,
    VideoPreviewHandler,
    ArchivePreviewHandler,
    HexPreviewHandler,
)


class PreviewManager:
    """Manages all preview handlers."""

    def __init__(self):
        self.handlers = []
        self._register_default_handlers()

    def _register_default_handlers(self):
        self.handlers.extend([
            TextPreviewHandler(),
            CodePreviewHandler(),
            PDFPreviewHandler(),
            ExcelPreviewHandler(),
            CSVPreviewHandler(),
            WordPreviewHandler(),
            PowerPointPreviewHandler(),
            AudioPreviewHandler(),
            VideoPreviewHandler(),
            ArchivePreviewHandler(),
            HexPreviewHandler(),
        ])

    def get_handler(self, file_path):
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler
        return None

    def generate_preview(self, file_path, max_size=1024*1024):
        """Generate preview using appropriate handler. Returns PreviewResult."""
        handler = self.get_handler(file_path)
        if handler:
            result = handler.generate_preview(file_path, max_size)
            return PreviewResult(*result) if not isinstance(result, PreviewResult) else result
        return PreviewResult("error", "No preview handler available for this file type", {})
