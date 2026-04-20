from pydantic import BaseModel, Field
from typing import Optional


class CMLRow(BaseModel):
    # source tracking
    source_file: str = ""
    source_sheet: str = ""
    source_row: int = 0  # 1-indexed Excel row number for write-back
    file_modified: float = 0.0  # timestamp for precedence

    # system-level fields
    system_path: str = ""
    system_name: str = ""
    system_type: str = "Process Piping"
    equipment_type: str = ""
    equipment_id: str = ""

    # CML data fields (columns A-T)
    cml: str = ""
    cml_location: str = ""
    component_type: str = ""
    component: str = ""
    od: str = ""
    nom: str = ""
    ca: str = ""
    tmin: str = ""
    mat_spec: str = ""
    mat_grade: str = ""
    pressure: str = ""
    temp: str = ""
    je: str = ""
    access: str = ""
    insulation: str = ""
    install_date: str = ""
    status: str = ""
    nde: str = ""
    ut_reading: str = ""
    inspection_notes: str = ""
    inspected_by: str = ""

    # file-level metadata
    material_type: str = "Carbon"  # "Carbon", "Stainless", or "Mixed" (CS & SS circuit), from UT sheet D4

    # validation
    warnings: list[str] = Field(default_factory=list)
    is_valid: bool = True


class EntityInfoRow(BaseModel):
    source_file: str = ""
    source_pdf: str = ""
    system_path: str = ""
    system_name: str = ""
    system_type: str = "Process Piping"
    equipment_id: str = ""
    equipment_description: str = ""
    joint_efficiency: str = "1.0"
    year_built: str = ""
    in_service: str = "Yes"
    in_service_date: str = ""
    class_name: str = "Class 2"
    stress_table_used: str = ""
    pid_drawing: str = "No"
    pid_number: str = ""
    pfd: str = "No"
    pfd_number: str = ""
    psm_covered: str = "Yes"
    diameter: str = ""
    process_service: str = ""
    warnings: list[str] = Field(default_factory=list)
    field_sources: dict[str, str] = Field(default_factory=dict)
    is_valid: bool = True


class FileEntry(BaseModel):
    # represents a file in the file list
    file_path: str
    filename: str = ""
    folder: str = ""
    system_name: str = ""
    status: str = "Pending"  # Pending, Parsed, Error, Missing
    row_count: int = 0
    error_message: str = ""
    modified_time: float = 0.0

    def model_post_init(self, __context) -> None:
        import os
        if not self.filename:
            self.filename = os.path.basename(self.file_path)
        if not self.folder:
            self.folder = os.path.dirname(self.file_path)
        if not self.modified_time and os.path.exists(self.file_path):
            self.modified_time = os.path.getmtime(self.file_path)
