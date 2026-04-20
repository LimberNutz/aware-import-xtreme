from dataclasses import dataclass, field


@dataclass
class AppConfig:
    # system path entered in UI, applied to all rows
    system_path: str = ""
    # True = standard 1.01 style, False = client 1.1 style
    standard_cml_style: bool = True
    # last used directory for file picker
    last_directory: str = ""
    # window geometry
    window_width: int = 1400
    window_height: int = 850
