# Design Document CSV Builder (Aware IDMS)

**Location:** [Project Folder](<file:///C:/Users/cherr/Desktop/Codes/AwareImport/DesignDocImporter>)


## Overview

This utility scans a CAD drawing directory and automatically builds a CSV for **Aware IDMS Design Document import**.

It is designed for real-world inspection workflows where:

* DWG files are stored in a main **CAD folder**
* PDF files are stored in a **subfolder (e.g., "CAD PDF")**
* File names follow a consistent naming pattern (e.g., `GG-DIS-01 ...`)

---

## What This Tool Does

* Recursively scans a directory for:

  * `.dwg` files (CAD drawings)
  * `.pdf` files (typically model exports)
* Automatically extracts **entity names** from filenames
* Matches files to entities based on filename prefix
* Generates a CSV formatted for Aware import

---

## Folder Structure (Expected)

```text
CAD\
  GG-DIS-01 CAD SHT 1.dwg
  GG-DIS-01 CAD SHT 2.dwg
  ...
  CAD PDF\
    GG-DIS-01 CAD SHT 1-Model.pdf
    GG-DIS-01 CAD SHT 2-Model.pdf
```

✔ This structure is fully supported
✔ No restructuring required

---

## How Matching Works

A file is matched to an entity if:

* The filename **starts with the entity name**

### Example (Valid Matches)

```text
GG-DIS-01 CAD SHT 1.dwg
GG-DIS-01 CAD SHT 2.dwg
GG-DIS-01 CAD SHT 1-Model.pdf
```

### Example (Invalid Matches)

```text
SHT1_GG-DIS-01.dwg
DRAWING-GG-DIS-01.pdf
```

---

## Document Type Logic

| File Type | Condition                   | Output Type              |
| --------- | --------------------------- | ------------------------ |
| PDF       | Filename ends with `-Model` | `Inspection Drawing PDF` |
| DWG       | All DWG files               | `Inspection Drawing`     |
| PDF       | Anything else               | `Inspection Drawing`     |

---

## Output Format

The script generates a CSV with these columns:

```text
SystemPath
Design Documents.Document
Design Documents.Document Type
Design Documents.Document Description
```

---

## Output Filename Format

```text
Equip_CADimport_<ProjectName>_<YYYYMMDD>.csv
```

### Example

```text
Equip_CADimport_GoldenGrain_20260417.csv
```

---

## Config File Setup

Create a file like:

```text
job_config.txt
```

### Example Config

```text
ROOT_DIR=C:\Users\cherr\Desktop\1. Working Projects\Golden Grain\CAD
SYSTEM_PATH_BASE=XCEL > Golden Grain Energy > Mason City, IA > Unit > Piping >
MAX_DEPTH=2
OUTPUT_DIR=C:\Users\cherr\Desktop\1. Working Projects\Golden Grain\Exports
PROJECT_NAME=GoldenGrain

AUTO_DISCOVER_ENTITIES=true
IGNORE_RECOVER_FILES=true
PREFER_DWG_FOR_ENTITY_DISCOVERY=true
```

---

## Config Fields

### Required

| Field            | Description                          |
| ---------------- | ------------------------------------ |
| ROOT_DIR         | Root CAD folder (NOT the PDF folder) |
| SYSTEM_PATH_BASE | Base Aware SystemPath                |

---

### Optional

| Field                           | Description                                  |
| ------------------------------- | -------------------------------------------- |
| PROJECT_NAME                    | Used in output filename                      |
| OUTPUT_DIR                      | Where CSV will be saved                      |
| OUTPUT_FILENAME                 | Overrides automatic naming                   |
| MAX_DEPTH                       | Folder depth to scan (recommended: 2)        |
| AUTO_DISCOVER_ENTITIES          | Automatically detect entities from filenames |
| IGNORE_RECOVER_FILES            | Skips `_recover.dwg` files                   |
| PREFER_DWG_FOR_ENTITY_DISCOVERY | Uses DWGs as primary entity source           |

---

## How to Run

### Config Mode (Recommended)

```bash
python design_doc_csv_builder.py job_config.txt
```

---

### Interactive Mode

```bash
python design_doc_csv_builder.py
```

Prompts for:

* Root directory
* SystemPath
* Project name

---

## Behavior Details

* Searches all folders up to `MAX_DEPTH`
* Includes BOTH:

  * DWG files (root CAD folder)
  * PDF files (subfolders like `CAD PDF`)
* Does NOT limit results to one folder depth
* Automatically removes duplicate entities
* Ignores files containing `_recover`

---

## Important Rules

### Always Set ROOT_DIR to the CAD Folder

```text
✔ Correct:
...\Golden Grain\CAD

❌ Wrong:
...\Golden Grain\CAD\CAD PDF
```

---

### Entity Names Are Derived Automatically

You do NOT need to provide:

```text
GG-DIS-01 CAD SHT 1
```

The script extracts:

```text
GG-DIS-01
```

---

## Example Output

```text
SystemPath,...,Document,Type,Description
... > GG-DIS-01,GG-DIS-01 CAD SHT 1-Model.pdf,Inspection Drawing PDF,...
... > GG-DIS-01,GG-DIS-01 CAD SHT 2-Model.pdf,Inspection Drawing PDF,...
... > GG-DIS-01,GG-DIS-01 CAD SHT 1.dwg,Inspection Drawing,...
... > GG-DIS-01,GG-DIS-01 CAD SHT 2.dwg,Inspection Drawing,...
```

---

## Troubleshooting

### PDFs Not Showing Up

* Verify they are inside a subfolder under ROOT_DIR
* Increase MAX_DEPTH if needed

---

### Missing Entities

* Ensure filenames START with entity name
* Check for naming inconsistencies

---

### No Output File

* Verify OUTPUT_DIR exists or is writable
* If not set, file is written to script directory

---

## Safety

This script is **read-only** for your files.

✔ Does NOT move files
✔ Does NOT modify files
✔ Does NOT upload anything

It only generates a CSV.

---

## Summary

```text
1. Point ROOT_DIR to CAD folder
2. Run script
3. Import CSV into Aware
```

---

## Future Enhancements (Optional)

* Audit report (missing DWG/PDF pairs)
* SharePoint upload automation
* Direct Aware API integration

---
