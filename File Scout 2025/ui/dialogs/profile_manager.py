from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QPushButton, QDialogButtonBox, QInputDialog,
                             QMessageBox, QWidget)

from config import get_settings


class ProfileManagerDialog(QDialog):
    """A dialog for managing saved search profiles."""
    def __init__(self, parent=None, zoom_level=100):
        super().__init__(parent)
        self.setWindowTitle("Profile Manager")
        self.setMinimumSize(400, 300)
        self.settings = get_settings()
        self.zoom_level = zoom_level

        layout = QVBoxLayout(self)
        self.profile_list = QListWidget()
        self.profile_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.profile_list)
        button_layout = QHBoxLayout()
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_profile)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_profile)
        button_layout.addWidget(self.rename_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        self.dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel)
        self.dialog_buttons.accepted.connect(self.accept)
        self.dialog_buttons.rejected.connect(self.reject)
        button_layout.addWidget(self.dialog_buttons)
        layout.addLayout(button_layout)
        self.load_profiles()

        # Apply zoom from parent window AFTER UI is created
        if zoom_level != 100:
            self._apply_zoom()

    def _apply_zoom(self):
        """Apply zoom level to all dialog elements"""
        # Calculate new font size based on zoom
        base_font_size = 9
        new_font_size = int(base_font_size * (self.zoom_level / 100))

        # Create font for the dialog
        app_font = self.font()
        app_font.setPointSize(new_font_size)

        # Apply to dialog and all widgets
        self.setFont(app_font)

        # Update all child widgets
        for widget in self.findChildren(QWidget):
            widget.setFont(app_font)

    def load_profiles(self):
        self.profile_list.clear()
        profiles = self.settings.value("profiles", {})
        for name in sorted(profiles.keys()):
            self.profile_list.addItem(name)

    def rename_profile(self):
        current_item = self.profile_list.currentItem()
        if not current_item: return
        old_name = current_item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Profile", "New profile name:", text=old_name)
        if ok and new_name and new_name != old_name:
            profiles = self.settings.value("profiles", {})
            if new_name in profiles:
                QMessageBox.warning(self, "Name Exists", "A profile with this name already exists.")
                return
            profiles[new_name] = profiles.pop(old_name)
            self.settings.setValue("profiles", profiles)
            self.load_profiles()

    def delete_profile(self):
        current_item = self.profile_list.currentItem()
        if not current_item: return
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete the profile '{current_item.text()}'?")
        if reply == QMessageBox.StandardButton.Yes:
            profiles = self.settings.value("profiles", {})
            profiles.pop(current_item.text(), None)
            self.settings.setValue("profiles", profiles)
            self.load_profiles()

    def get_selected_profile_name(self):
        return self.profile_list.currentItem().text() if self.profile_list.currentItem() else None
