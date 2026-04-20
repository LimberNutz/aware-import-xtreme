from PyQt6.QtCore import QSettings
from constants import SETTINGS_ORG, SETTINGS_APP


def get_settings():
    return QSettings(SETTINGS_ORG, SETTINGS_APP)
