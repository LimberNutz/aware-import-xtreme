from collections import namedtuple

APP_NAME = "File Scout"
APP_VERSION = "3.3"
SETTINGS_ORG = "SBC-SoftwareByChris"
SETTINGS_APP = "FileScout"

MAX_RESULTS = 50000
MAX_SCAN_FILES = 1000000
LARGE_DIR_THRESHOLD = 100000

PreviewResult = namedtuple('PreviewResult', ['content_type', 'data', 'metadata'])

ICON_SEARCH = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTE1LjUgMTRoLS43OWwtLjI4LS4yN0E2LjQ3MSA2LjQ3MSAwIDAgMCAxNiA5LjVDMTYgNS45MSAxMy4wOSAzIDkuNSAzUzMgNS45MSAzIDkuNSA1LjkxIDE2IDkuNSAxNmMxLjQzIDAgMi43Ni0uNDcgMy45MS0xLjI1bC4yNy4yOHYuNzlsNSA0Ljk5TDIwLjQ9IDE5bC00Ljk5LTV6bS02IDBDNy4wMSAxNCA1IDExLjk5IDUgOS41UzcuMDEgNSA5LjUgNSAxNCA3LjAxIDE0IDkuNSAxMS45OSAxNCA5LjUgMTR6Ii8+PC9zdmc+"
ICON_STOP = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTYgNmgxMnYxMkg2eiIvPjwvc3ZnPg=="
ICON_EXPORT = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2ZmZmZmZiI+PHBhdGggZD0iTTE5IDEydjdINVYzdjloMlY5aDEwbDd2NGgtMnpNOCA1djhoOFY5SDh6bS0yIDE2aDEydjJIMFYxMmg0djlaIi8+PC9zdmc+"

EXCLUDED_EXTENSIONS = {'.bak', '.log', '.ini', '.dwl', '.dwl2', '.tmp', '.lnk', '.db'}

FILE_TYPE_MAPPINGS = {
    "All Files": [], "Documents": ["doc", "docx", "pdf", "txt", "rtf", "odt", "pages"],
    "Spreadsheets": ["xls", "xlsx", "csv", "xlsm", "xlsb", "ods", "numbers"],
    "Presentations": ["ppt", "pptx", "pptm", "key"], "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg", "heic"],
    "CAD Files": ["dwg", "dxf", "dwf", "rvt", "rfa", "dgn"], "Archives": ["zip", "rar", "7z", "tar", "gz", "bz2"]
}
