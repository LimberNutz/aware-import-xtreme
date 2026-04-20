#!/usr/bin/env python3
"""Project Blueprint — Snapshot Generator

Produces deterministic, token-efficient snapshots of the project state.
Zero external dependencies — uses only the Python standard library.

Usage:
    python tools/blueprint/snapshot.py
"""

import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Directories/files to exclude from the tree
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".hg", ".svn", "node_modules", "venv", ".venv",
    "env", ".env", "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    ".eggs", "*.egg-info", ".idea", ".vscode", ".DS_Store",
}

EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db", "desktop.ini",
}

EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".xlsm", ".xlsx", ".xls", ".docx", ".doc", ".pptx",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".mp3", ".mp4", ".wav", ".avi",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_project_root():
    """Walk up from this script to find the project root (contains main.py or requirements.txt)."""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.exists(os.path.join(d, "requirements.txt")) or os.path.exists(os.path.join(d, "main.py")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # fallback: two levels up from tools/blueprint/
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def should_exclude_dir(name):
    return name in EXCLUDE_DIRS or name.endswith(".egg-info")


def should_exclude_file(name):
    if name in EXCLUDE_FILES:
        return True
    _, ext = os.path.splitext(name)
    return ext.lower() in EXCLUDE_EXTENSIONS


def iter_source_files(root, extensions=(".py", ".js", ".ts", ".tsx")):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        for fname in filenames:
            if should_exclude_file(fname):
                continue
            if extensions and not fname.endswith(extensions):
                continue
            yield os.path.join(dirpath, fname)


def read_text(path, limit=None):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit) if limit else f.read()
    except Exception:
        return ""


def relpath(path, root):
    return os.path.relpath(path, root).replace("\\", "/")


def summarize_text(text, max_len=100):
    text = re.sub(r"\s+", " ", text).strip(" -#>\t")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def parse_python_symbols(content):
    class_names = []
    public_functions = []
    qsettings_keys = []

    for line in content.splitlines():
        class_match = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\b", line)
        if class_match:
            class_names.append(class_match.group(1))

        func_match = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\b", line)
        if func_match:
            name = func_match.group(1)
            if not name.startswith("_"):
                public_functions.append(name)

        for key in re.findall(r"(?:QSettings\([^\n]*?\)|[A-Za-z_][A-Za-z0-9_]*)\.(?:value|setValue)\(\s*[\"']([^\"']+)[\"']", line):
            qsettings_keys.append(key)

    return class_names, public_functions, qsettings_keys


def extract_doc_summary(path):
    text = read_text(path)
    if not text:
        return "(unreadable)"

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return summarize_text(stripped.lstrip("#").strip())
        return summarize_text(stripped)

    return "(empty)"


def detect_architecture(root):
    lines = ["# Architecture Detection (auto-detected)", ""]
    top_dirs = {
        name for name in os.listdir(root)
        if os.path.isdir(os.path.join(root, name)) and not should_exclude_dir(name)
    }

    architecture_labels = []
    if {"ui", "services", "models"}.issubset(top_dirs):
        architecture_labels.append("Layered application: ui/ + services/ + models/")
    if os.path.exists(os.path.join(root, "main.py")):
        main_text = read_text(os.path.join(root, "main.py"), limit=4096)
        if "QApplication" in main_text:
            architecture_labels.append("Desktop GUI bootstrap in main.py (Qt application)")
        main_imports = re.findall(r"^from\s+([A-Za-z_][\w.]*)\s+import\s+(.+)$", main_text, flags=re.MULTILINE)
        for module, names in main_imports[:5]:
            if module.startswith("ui"):
                architecture_labels.append(f"Primary UI entry imports {module}: {summarize_text(names, 60)}")

    if os.path.exists(os.path.join(root, "docs", "00_BLUEPRINT.md")):
        architecture_labels.append("Blueprint documentation present: docs/00_BLUEPRINT.md")

    if architecture_labels:
        for label in architecture_labels:
            lines.append(f"- {label}")
    else:
        lines.append("- No strong architecture pattern detected")

    lines.append("")
    lines.append("## Directory roles")
    role_hints = {
        "app": "application config/constants",
        "models": "domain models / data contracts",
        "services": "parsing, transformation, export, worker logic",
        "ui": "Qt widgets, dialogs, and orchestration",
        "utils": "shared helpers",
        "docs": "blueprints, contracts, and reference docs",
        "tools": "developer tooling / project utilities",
    }
    for dirname in sorted(top_dirs):
        if dirname in role_hints:
            lines.append(f"- {dirname}/: {role_hints[dirname]}")

    return "\n".join(lines)


def detect_api_surface(root):
    lines = ["# API Surface (auto-detected)", ""]
    interesting_dirs = ("app", "models", "services", "ui", "utils")
    found = False

    for dirname in interesting_dirs:
        dirpath = os.path.join(root, dirname)
        if not os.path.isdir(dirpath):
            continue
        module_lines = []
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith(".py") or should_exclude_file(fname):
                continue
            path = os.path.join(dirpath, fname)
            content = read_text(path)
            class_names, public_functions, _ = parse_python_symbols(content)
            parts = []
            if class_names:
                parts.append("classes=" + ", ".join(class_names[:4]))
            if public_functions:
                parts.append("functions=" + ", ".join(public_functions[:5]))
            if parts:
                found = True
                module_lines.append(f"- {dirname}/{fname}: " + "; ".join(parts))
        if module_lines:
            lines.append(f"## {dirname}/")
            lines.extend(module_lines[:8])
            lines.append("")

    if not found:
        lines.append("No public API symbols detected.")

    return "\n".join(lines)


def detect_config_patterns(root):
    lines = ["# Configuration Patterns (auto-detected)", ""]
    config_files = []
    for candidate in ("app/config.py", "app/constants.py", ".env", "settings.py", "config.py"):
        if os.path.exists(os.path.join(root, candidate)):
            config_files.append(candidate)

    if config_files:
        lines.append("## Config files")
        for path in config_files:
            lines.append(f"- {path}")
        lines.append("")

    qsettings_counter = Counter()
    app_config_fields = []
    for path in iter_source_files(root, extensions=(".py",)):
        content = read_text(path)
        _, _, keys = parse_python_symbols(content)
        for key in keys:
            qsettings_counter[key] += 1

        if relpath(path, root) == "app/config.py":
            for line in content.splitlines():
                field_match = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*[^=]+=", line)
                if field_match:
                    app_config_fields.append(field_match.group(1))

    if qsettings_counter:
        lines.append("## QSettings keys")
        for key, count in qsettings_counter.most_common(12):
            lines.append(f"- {key} (seen {count} time{'s' if count != 1 else ''})")
        lines.append("")

    if app_config_fields:
        lines.append("## AppConfig fields")
        for field in app_config_fields:
            lines.append(f"- {field}")
        lines.append("")

    if not config_files and not qsettings_counter and not app_config_fields:
        lines.append("No notable configuration patterns detected.")

    return "\n".join(lines)


def detect_integrations(root):
    lines = ["# External Integrations (auto-detected)", ""]
    integration_hits = defaultdict(list)
    pattern_map = {
        r"openpyxl": "Excel workbook I/O",
        r"pypdf|PyPDF": "PDF parsing",
        r"csv": "CSV read/write",
        r"send2trash": "Safe file deletion",
        r"os\.startfile|explorer": "Windows shell integration",
        r"json": "JSON session/config persistence",
        r"QSettings": "Windows Registry persistence via QSettings",
        r"thefuzz|fuzz": "Fuzzy matching",
    }

    for path in iter_source_files(root, extensions=(".py",)):
        content = read_text(path, limit=12000)
        rel = relpath(path, root)
        for pattern, label in pattern_map.items():
            if re.search(pattern, content, flags=re.IGNORECASE):
                integration_hits[label].append(rel)

    for label in sorted(integration_hits):
        sample_files = ", ".join(sorted(integration_hits[label])[:4])
        lines.append(f"- {label}: {sample_files}")

    if not integration_hits:
        lines.append("No notable integrations detected.")

    return "\n".join(lines)


def detect_data_flow(root):
    lines = ["# Data Flow Hints (auto-detected)", ""]
    import_edges = defaultdict(set)
    incoming = Counter()
    local_modules = set()

    for path in iter_source_files(root, extensions=(".py",)):
        rel = relpath(path, root)
        module = rel[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        if module:
            local_modules.add(module)

    for path in iter_source_files(root, extensions=(".py",)):
        rel = relpath(path, root)
        module = rel[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        content = read_text(path, limit=16000)
        for imported in re.findall(r"^from\s+([A-Za-z_][\w.]*)\s+import\s+", content, flags=re.MULTILINE):
            for candidate in local_modules:
                if imported == candidate or imported.startswith(candidate + ".") or candidate.startswith(imported + "."):
                    import_edges[module].add(candidate)
        for imported in re.findall(r"^import\s+([A-Za-z_][\w.]*)", content, flags=re.MULTILINE):
            for candidate in local_modules:
                if imported == candidate or candidate.startswith(imported + "."):
                    import_edges[module].add(candidate)

    for source, targets in import_edges.items():
        for target in targets:
            incoming[target] += 1

    main_targets = sorted(import_edges.get("main", []))
    if main_targets:
        lines.append("## Main entry imports")
        for target in main_targets[:8]:
            lines.append(f"- main -> {target}")
        lines.append("")

    if incoming:
        lines.append("## Most referenced local modules")
        for module, count in incoming.most_common(10):
            if module:
                lines.append(f"- {module} (imported by {count} module{'s' if count != 1 else ''})")
        lines.append("")

    leaves = sorted(module for module, targets in import_edges.items() if module and not targets)
    if leaves:
        lines.append("## Leaf modules")
        for module in leaves[:8]:
            lines.append(f"- {module}")

    if not main_targets and not incoming and not leaves:
        lines.append("No data-flow hints detected.")

    return "\n".join(lines)


def detect_docs_index(root):
    lines = ["# Documentation Index (auto-detected)", ""]
    docs = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        for fname in filenames:
            if fname.endswith(".md") and not should_exclude_file(fname):
                path = os.path.join(dirpath, fname)
                docs.append((relpath(path, root), extract_doc_summary(path)))

    if docs:
        for path, summary in sorted(docs)[:20]:
            lines.append(f"- {path}: {summary}")
    else:
        lines.append("No Markdown documentation files detected.")

    return "\n".join(lines)


def synthesize_how_it_works(root):
    """Synthesize an opinionated 'How this app works' summary from detected signals."""
    lines = ["# How This App Works (synthesized)", ""]
    
    # Detect key characteristics
    is_qt_gui = False
    is_layered = False
    has_excel = False
    has_pdf = False
    has_csv = False
    has_qsettings = False
    has_json_sessions = False
    has_fuzzy = False
    
    # Quick scans
    for path in iter_source_files(root, extensions=(".py",)):
        content = read_text(path, limit=8000)
        if "QApplication" in content:
            is_qt_gui = True
        if "openpyxl" in content:
            has_excel = True
        if "pypdf" in content or "PyPDF" in content:
            has_pdf = True
        if "csv" in content:
            has_csv = True
        if "QSettings" in content:
            has_qsettings = True
        if "json" in content:
            has_json_sessions = True
        if "thefuzz" in content or "fuzz" in content:
            has_fuzzy = True
    
    # Check for layered architecture
    top_dirs = {
        name for name in os.listdir(root)
        if os.path.isdir(os.path.join(root, name)) and not should_exclude_dir(name)
    }
    if {"ui", "services", "models"}.issubset(top_dirs):
        is_layered = True
    
    # Synthesize bullets based on detected patterns
    bullets = []
    
    # Purpose inference
    blueprint_path = os.path.join(root, "docs", "00_BLUEPRINT.md")
    if os.path.exists(blueprint_path):
        blueprint_head = read_text(blueprint_path, limit=500)
        if "batch" in blueprint_head.lower() and "parse" in blueprint_head.lower():
            bullets.append("Batch parsing tool — processes multiple input files and exports structured output")
    
    # Architecture
    if is_qt_gui:
        bullets.append("Desktop GUI application (PySide6/Qt) — user interacts via windowed interface")
    if is_layered:
        bullets.append("Layered architecture — UI layer (ui/) → business logic (services/) → data models (models/)")
    
    # Data flow
    if has_excel:
        bullets.append("Primary input: Excel workbooks (.xlsx/.xlsm) — parsed via openpyxl")
    if has_pdf:
        bullets.append("Secondary input: PDF documents — extracted via pypdf for metadata/fallback")
    if has_csv:
        bullets.append("Primary output: CSV files — formatted for downstream import systems")
    
    # Processing
    if has_fuzzy:
        bullets.append("Fuzzy matching — uses thefuzz to correlate entities across data sources")
    
    # Persistence
    if has_qsettings and has_json_sessions:
        bullets.append("Persistence: QSettings (Windows Registry) for UI state + JSON session files for workspace")
    elif has_qsettings:
        bullets.append("Persistence: QSettings (Windows Registry) for configuration")
    elif has_json_sessions:
        bullets.append("Persistence: JSON session files for workspace state")
    
    # Worker pattern
    for path in iter_source_files(root, extensions=(".py",)):
        content = read_text(path, limit=4000)
        if "QThread" in content:
            bullets.append("Background processing — uses QThread workers to keep UI responsive during file operations")
            break
    
    # Domain models
    for path in iter_source_files(root, extensions=(".py",)):
        content = read_text(path, limit=4000)
        if "BaseModel" in content and "pydantic" in content.lower():
            bullets.append("Data models: Pydantic BaseModel classes enforce schema validation")
            break
    
    if not bullets:
        bullets.append("No strong synthesis signals detected")
    
    for bullet in bullets[:8]:
        lines.append(f"- {bullet}")
    
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: tree.txt
# ---------------------------------------------------------------------------

def generate_tree(root):
    lines = []
    root_name = os.path.basename(root) or root

    def walk(directory, prefix=""):
        entries = sorted(os.listdir(directory))
        dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e)) and not should_exclude_dir(e)]
        files = [e for e in entries if os.path.isfile(os.path.join(directory, e)) and not should_exclude_file(e)]

        all_items = [(f, False) for f in files] + [(d, True) for d in dirs]
        for i, (name, is_dir) in enumerate(all_items):
            is_last = i == len(all_items) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if is_dir else ""
            lines.append(f"{prefix}{connector}{name}{suffix}")
            if is_dir:
                extension = "    " if is_last else "│   "
                walk(os.path.join(directory, name), prefix + extension)

    lines.append(f"{root_name}/")
    walk(root)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: entrypoints.txt
# ---------------------------------------------------------------------------

def detect_entrypoints(root):
    lines = ["# Entry Points (auto-detected)", ""]

    # Check for main.py
    main_py = os.path.join(root, "main.py")
    if os.path.exists(main_py):
        lines.append(f"GUI Entry: python main.py")
        # Try to find the main() call
        try:
            with open(main_py, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if "QApplication" in content:
                lines.append("  Type: PySide6/Qt GUI application")
            if 'if __name__' in content:
                lines.append("  Guard: if __name__ == '__main__'")
        except Exception:
            pass
        lines.append("")

    # Check for manage.py (Django)
    manage_py = os.path.join(root, "manage.py")
    if os.path.exists(manage_py):
        lines.append("Django: python manage.py")

    # Check for setup.py / pyproject.toml console_scripts
    for fname in ("setup.py", "pyproject.toml", "setup.cfg"):
        fpath = os.path.join(root, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if "console_scripts" in content or "scripts" in content:
                    lines.append(f"Console scripts defined in: {fname}")
            except Exception:
                pass

    # Check for package.json scripts
    pkg_json = os.path.join(root, "package.json")
    if os.path.exists(pkg_json):
        try:
            import json
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if scripts:
                lines.append("npm scripts:")
                for name, cmd in sorted(scripts.items()):
                    lines.append(f"  {name}: {cmd}")
        except Exception:
            pass

    # Check for Makefile targets
    makefile = os.path.join(root, "Makefile")
    if os.path.exists(makefile):
        try:
            with open(makefile, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = re.match(r"^([a-zA-Z_][\w-]*)\s*:", line)
                    if m:
                        lines.append(f"make {m.group(1)}")
        except Exception:
            pass

    # Check for Dockerfile
    if os.path.exists(os.path.join(root, "Dockerfile")):
        lines.append("Docker: Dockerfile present")

    if len(lines) <= 2:
        lines.append("No entry points detected.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: deps.txt
# ---------------------------------------------------------------------------

def detect_deps(root):
    lines = ["# Dependencies (auto-detected)", ""]
    found = False

    # requirements.txt
    req_path = os.path.join(root, "requirements.txt")
    if os.path.exists(req_path):
        found = True
        lines.append("## requirements.txt")
        try:
            with open(req_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lines.append(f"  {line}")
        except Exception:
            lines.append("  (read error)")
        lines.append("")

    # pyproject.toml
    pyproject = os.path.join(root, "pyproject.toml")
    if os.path.exists(pyproject):
        found = True
        lines.append("## pyproject.toml (dependencies section)")
        try:
            with open(pyproject, "r", encoding="utf-8", errors="replace") as f:
                in_deps = False
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("[") and "dependencies" in stripped.lower():
                        in_deps = True
                        lines.append(f"  {stripped}")
                        continue
                    if in_deps:
                        if stripped.startswith("["):
                            in_deps = False
                            continue
                        if stripped:
                            lines.append(f"  {stripped}")
        except Exception:
            lines.append("  (read error)")
        lines.append("")

    # package.json
    pkg_json = os.path.join(root, "package.json")
    if os.path.exists(pkg_json):
        found = True
        try:
            import json
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            for section in ("dependencies", "devDependencies"):
                deps = pkg.get(section, {})
                if deps:
                    lines.append(f"## package.json [{section}]")
                    for name, ver in sorted(deps.items()):
                        lines.append(f"  {name}: {ver}")
                    lines.append("")
        except Exception:
            lines.append("  (read error)")

    # Cargo.toml
    cargo = os.path.join(root, "Cargo.toml")
    if os.path.exists(cargo):
        found = True
        lines.append("## Cargo.toml (dependencies)")
        try:
            with open(cargo, "r", encoding="utf-8", errors="replace") as f:
                in_deps = False
                for line in f:
                    stripped = line.strip()
                    if stripped == "[dependencies]":
                        in_deps = True
                        continue
                    if in_deps:
                        if stripped.startswith("["):
                            in_deps = False
                            continue
                        if stripped:
                            lines.append(f"  {stripped}")
        except Exception:
            lines.append("  (read error)")
        lines.append("")

    # go.mod
    gomod = os.path.join(root, "go.mod")
    if os.path.exists(gomod):
        found = True
        lines.append("## go.mod")
        try:
            with open(gomod, "r", encoding="utf-8", errors="replace") as f:
                lines.append(f"  {f.read().strip()}")
        except Exception:
            pass
        lines.append("")

    if not found:
        lines.append("No dependency files detected.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: db.txt
# ---------------------------------------------------------------------------

def detect_db(root):
    lines = ["# Database Detection (auto-detected)", ""]
    found = False

    # Look for common ORM/DB indicators
    db_indicators = {
        "models.py": "Django/Flask models",
        "schema.prisma": "Prisma schema",
        "alembic.ini": "Alembic migrations",
        "schema.sql": "SQL schema",
        "migrations": "Migrations directory",
        "knexfile.js": "Knex.js config",
        "ormconfig.json": "TypeORM config",
        "ormconfig.ts": "TypeORM config",
        "database.yml": "Database config",
    }

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded dirs
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        rel = os.path.relpath(dirpath, root)

        for fname in filenames:
            if fname in db_indicators:
                found = True
                lines.append(f"Found: {os.path.join(rel, fname)} ({db_indicators[fname]})")

        for dname in dirnames:
            if dname in db_indicators:
                found = True
                lines.append(f"Found: {os.path.join(rel, dname)}/ ({db_indicators[dname]})")

    # Check for SQLAlchemy, Django ORM, Prisma imports in Python files
    orm_patterns = [
        (r"from\s+sqlalchemy", "SQLAlchemy"),
        (r"from\s+django\.db", "Django ORM"),
        (r"from\s+peewee", "Peewee ORM"),
        (r"from\s+tortoise", "Tortoise ORM"),
        (r"import\s+mongoose", "Mongoose ODM"),
        (r"from\s+prisma", "Prisma"),
    ]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        for fname in filenames:
            if fname.endswith((".py", ".js", ".ts")):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(4096)  # only check first 4KB
                    for pattern, label in orm_patterns:
                        if re.search(pattern, content):
                            found = True
                            rel = os.path.relpath(fpath, root)
                            lines.append(f"ORM import: {label} in {rel}")
                            break
                except Exception:
                    pass

    if not found:
        lines.append("No database or ORM detected.")
        lines.append("This project uses in-memory data with optional JSON session files.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: tests.txt
# ---------------------------------------------------------------------------

def detect_tests(root):
    lines = ["# Test Infrastructure (auto-detected)", ""]
    found_dirs = []
    found_files = []

    test_dirs = {"tests", "test", "spec", "specs", "__tests__"}
    test_file_patterns = [
        re.compile(r"^test_.*\.py$"),
        re.compile(r"^.*_test\.py$"),
        re.compile(r"^.*\.test\.(js|ts|tsx)$"),
        re.compile(r"^.*\.spec\.(js|ts|tsx)$"),
    ]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        rel = os.path.relpath(dirpath, root)

        for dname in dirnames:
            if dname in test_dirs:
                found_dirs.append(os.path.join(rel, dname))

        for fname in filenames:
            for pat in test_file_patterns:
                if pat.match(fname):
                    found_files.append(os.path.join(rel, fname))
                    break

    if found_dirs:
        lines.append("## Test directories")
        for d in sorted(found_dirs):
            lines.append(f"  {d}/")
        lines.append("")

    if found_files:
        lines.append("## Test files")
        for f in sorted(found_files):
            lines.append(f"  {f}")
        lines.append("")

    # Check for test runners in config
    test_configs = {
        "pytest.ini": "pytest",
        "setup.cfg": "pytest (setup.cfg)",
        "tox.ini": "tox",
        "jest.config.js": "Jest",
        "jest.config.ts": "Jest",
        "vitest.config.ts": "Vitest",
        "karma.conf.js": "Karma",
        ".mocharc.yml": "Mocha",
    }

    for fname, runner in test_configs.items():
        if os.path.exists(os.path.join(root, fname)):
            lines.append(f"Config: {fname} ({runner})")

    # Check pyproject.toml for pytest config
    pyproject = os.path.join(root, "pyproject.toml")
    if os.path.exists(pyproject):
        try:
            with open(pyproject, "r", encoding="utf-8", errors="replace") as f:
                if "[tool.pytest" in f.read():
                    lines.append("Config: pyproject.toml [tool.pytest]")
        except Exception:
            pass

    if not found_dirs and not found_files:
        lines.append("No test directories or test files detected.")
        lines.append("")
        lines.append("Recommended: create tests/ with pytest")
        lines.append("  pip install pytest")
        lines.append("  python -m pytest tests/")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: env.txt
# ---------------------------------------------------------------------------

def detect_env(root):
    lines = ["# Environment Files (auto-detected)", ""]
    found = False

    env_patterns = [
        ".env", ".env.local", ".env.development", ".env.production",
        ".env.test", ".env.example", ".env.sample", ".env.template",
        "env.example", "env.sample",
    ]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        rel = os.path.relpath(dirpath, root)

        for fname in filenames:
            if fname in env_patterns or fname.startswith(".env"):
                fpath = os.path.join(dirpath, fname)
                found = True
                lines.append(f"## {os.path.join(rel, fname)}")
                lines.append("Keys (values redacted):")
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                key = line.split("=", 1)[0].strip()
                                lines.append(f"  {key}=***")
                            else:
                                lines.append(f"  {line}")
                except Exception:
                    lines.append("  (read error)")
                lines.append("")

    if not found:
        lines.append("No .env files detected.")
        lines.append("This project uses QSettings (Windows Registry) for configuration persistence.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot: rehydrate_bundle.txt
# ---------------------------------------------------------------------------

def generate_rehydrate_bundle(root):
    """Compact rehydration bundle — under 200 lines, one-shot LLM context."""
    lines = []
    repo_name = os.path.basename(root) or "unknown"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines.append(f"# Rehydration Bundle — {repo_name}")
    lines.append(f"# Generated: {timestamp}")
    lines.append(f"# Regenerate: python tools/blueprint/snapshot.py")
    lines.append("")

    # --- Detected stack ---
    lines.append("## Stack")
    stack_items = []
    if os.path.exists(os.path.join(root, "requirements.txt")):
        stack_items.append("Python (pip)")
    if os.path.exists(os.path.join(root, "pyproject.toml")):
        stack_items.append("Python (pyproject)")
    if os.path.exists(os.path.join(root, "package.json")):
        stack_items.append("Node.js (npm)")
    if os.path.exists(os.path.join(root, "Cargo.toml")):
        stack_items.append("Rust (cargo)")
    if os.path.exists(os.path.join(root, "go.mod")):
        stack_items.append("Go")

    # Detect frameworks from imports
    framework_indicators = {
        "PySide6": "PySide6 (Qt GUI)",
        "PyQt5": "PyQt5 (Qt GUI)",
        "PyQt6": "PyQt6 (Qt GUI)",
        "flask": "Flask",
        "django": "Django",
        "fastapi": "FastAPI",
        "react": "React",
        "vue": "Vue.js",
        "express": "Express.js",
    }
    detected_frameworks = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        for fname in filenames:
            if fname.endswith((".py", ".js", ".ts", ".tsx")):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        head = f.read(2048)
                    for key, label in framework_indicators.items():
                        if key in head and label not in detected_frameworks:
                            detected_frameworks.add(label)
                except Exception:
                    pass
        if len(detected_frameworks) >= 3:
            break

    if detected_frameworks:
        stack_items.extend(sorted(detected_frameworks))

    if stack_items:
        for item in stack_items:
            lines.append(f"  - {item}")
    else:
        lines.append("  - Unknown / Needs confirmation")
    lines.append("")

    lines.append("## Architecture")
    architecture_content = [
        line.strip("- ")
        for line in detect_architecture(root).split("\n")
        if line.startswith("-")
    ]
    if architecture_content:
        for item in architecture_content[:5]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - No strong architecture pattern detected")
    lines.append("")

    lines.append("## How This App Works")
    how_it_works_content = [
        line.strip("- ")
        for line in synthesize_how_it_works(root).split("\n")
        if line.startswith("-")
    ]
    if how_it_works_content:
        for item in how_it_works_content[:8]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - No synthesis available")
    lines.append("")

    # --- Key directories ---
    lines.append("## Key Directories")
    try:
        top_entries = sorted(os.listdir(root))
        top_dirs = [e for e in top_entries
                    if os.path.isdir(os.path.join(root, e)) and not should_exclude_dir(e)]
        for d in top_dirs:
            # Count files in dir (non-recursive, non-excluded)
            subpath = os.path.join(root, d)
            try:
                count = sum(1 for f in os.listdir(subpath)
                            if os.path.isfile(os.path.join(subpath, f)) and not should_exclude_file(f))
            except Exception:
                count = 0
            lines.append(f"  {d}/  ({count} files)")
    except Exception:
        lines.append("  (could not list directories)")
    lines.append("")

    # --- Primary entry points ---
    lines.append("## Entry Points")
    entry_lines = detect_entrypoints(root).split("\n")
    for el in entry_lines:
        el = el.strip()
        if el and not el.startswith("#"):
            lines.append(f"  {el}")
    lines.append("")

    # --- Dependencies (compact) ---
    lines.append("## Dependencies (summary)")
    req_path = os.path.join(root, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lines.append(f"  {line}")
        except Exception:
            pass
    pkg_json = os.path.join(root, "package.json")
    if os.path.exists(pkg_json):
        try:
            import json
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            for section in ("dependencies", "devDependencies"):
                deps = pkg.get(section, {})
                for name, ver in sorted(deps.items()):
                    lines.append(f"  {name}: {ver}")
        except Exception:
            pass
    if not os.path.exists(req_path) and not os.path.exists(pkg_json):
        lines.append("  (none detected)")
    lines.append("")

    lines.append("## API Surface")
    api_lines = [line for line in detect_api_surface(root).split("\n") if line.startswith("-")]
    if api_lines:
        for line in api_lines[:8]:
            lines.append(f"  {line}")
    else:
        lines.append("  No public API symbols detected")
    lines.append("")

    lines.append("## Config / Persistence")
    config_lines = [line for line in detect_config_patterns(root).split("\n") if line.startswith("-")]
    if config_lines:
        for line in config_lines[:8]:
            lines.append(f"  {line}")
    else:
        lines.append("  No notable configuration patterns detected")
    lines.append("")

    lines.append("## Integrations")
    integration_lines = [line for line in detect_integrations(root).split("\n") if line.startswith("-")]
    if integration_lines:
        for line in integration_lines[:6]:
            lines.append(f"  {line}")
    else:
        lines.append("  No notable integrations detected")
    lines.append("")

    # --- Test commands ---
    lines.append("## Test Commands")
    test_cmds_found = False
    if os.path.exists(os.path.join(root, "pytest.ini")) or os.path.exists(os.path.join(root, "setup.cfg")):
        lines.append("  python -m pytest")
        test_cmds_found = True
    pyproject = os.path.join(root, "pyproject.toml")
    if os.path.exists(pyproject):
        try:
            with open(pyproject, "r", encoding="utf-8", errors="replace") as f:
                if "[tool.pytest" in f.read():
                    lines.append("  python -m pytest")
                    test_cmds_found = True
        except Exception:
            pass
    if os.path.exists(pkg_json):
        try:
            import json
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "test" in scripts:
                lines.append(f"  npm test  ({scripts['test']})")
                test_cmds_found = True
        except Exception:
            pass
    if not test_cmds_found:
        lines.append("  No test runner detected")
        lines.append("  Recommended: python -m pytest tests/")
    lines.append("")

    # --- DB/migrations ---
    lines.append("## DB / Migrations")
    db_lines = detect_db(root).split("\n")
    db_content = [dl.strip() for dl in db_lines if dl.strip() and not dl.strip().startswith("#")]
    if db_content:
        for dl in db_content[:5]:
            lines.append(f"  {dl}")
    else:
        lines.append("  None detected")
    lines.append("")

    lines.append("## Data Flow Hints")
    data_flow_lines = [line for line in detect_data_flow(root).split("\n") if line.startswith("-")]
    if data_flow_lines:
        for line in data_flow_lines[:8]:
            lines.append(f"  {line}")
    else:
        lines.append("  No data-flow hints detected")
    lines.append("")

    # --- Load-these-files-first list ---
    lines.append("## Load These Files First")
    lines.append("")
    lines.append("Priority 1 (always load):")
    priority_1 = [
        "docs/00_BLUEPRINT.md",
        ".llm/rules.md",
    ]
    for f in priority_1:
        exists = "ok" if os.path.exists(os.path.join(root, f)) else "MISSING"
        lines.append(f"  {f}  [{exists}]")

    lines.append("")
    lines.append("Priority 2 (load for non-trivial changes):")
    priority_2 = [
        "docs/INTERFACE_MAP.md",
        "docs/SAFE_CHANGELOG.md",
        "docs/DB_CONTRACT.md",
        "tools/blueprint/verify_before_merge.md",
    ]
    for f in priority_2:
        exists = "ok" if os.path.exists(os.path.join(root, f)) else "MISSING"
        lines.append(f"  {f}  [{exists}]")

    lines.append("")
    lines.append("Priority 3 (reference as needed):")
    priority_3 = [
        "docs/snapshots/tree.txt",
        "docs/snapshots/deps.txt",
        "docs/snapshots/entrypoints.txt",
        "docs/adr/0001-architecture-baseline.md",
        "tools/blueprint/change_request_template.md",
    ]
    for f in priority_3:
        exists = "ok" if os.path.exists(os.path.join(root, f)) else "MISSING"
        lines.append(f"  {f}  [{exists}]")
    lines.append("")

    # --- Env files ---
    lines.append("## Env Files")
    env_lines = detect_env(root).split("\n")
    env_content = [el.strip() for el in env_lines if el.strip() and not el.strip().startswith("#")]
    if env_content:
        for el in env_content[:5]:
            lines.append(f"  {el}")
    else:
        lines.append("  None detected")
    lines.append("")

    lines.append("## Documentation Index")
    doc_lines = [line for line in detect_docs_index(root).split("\n") if line.startswith("-")]
    if doc_lines:
        for line in doc_lines[:8]:
            lines.append(f"  {line}")
    else:
        lines.append("  No Markdown documentation files detected")
    lines.append("")

    # Truncate to stay under 200 lines
    if len(lines) > 198:
        lines = lines[:196]
        lines.append("  ... (truncated to 200 lines)")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    root = find_project_root()
    snap_dir = os.path.join(root, "docs", "snapshots")
    os.makedirs(snap_dir, exist_ok=True)

    snapshots = {
        "api_surface.txt": detect_api_surface,
        "architecture.txt": detect_architecture,
        "config_patterns.txt": detect_config_patterns,
        "data_flow.txt": detect_data_flow,
        "how_it_works.txt": synthesize_how_it_works,
        "tree.txt": generate_tree,
        "entrypoints.txt": detect_entrypoints,
        "deps.txt": detect_deps,
        "db.txt": detect_db,
        "docs_index.txt": detect_docs_index,
        "tests.txt": detect_tests,
        "env.txt": detect_env,
        "integrations.txt": detect_integrations,
        "rehydrate_bundle.txt": generate_rehydrate_bundle,
    }

    for filename, generator in sorted(snapshots.items()):
        filepath = os.path.join(snap_dir, filename)
        content = generator(root)
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content + "\n")
        print(f"  Generated: docs/snapshots/{filename}")

    print(f"\nAll snapshots written to: {os.path.relpath(snap_dir, root)}/")


if __name__ == "__main__":
    main()
