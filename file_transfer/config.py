"""
App configuration.

The settings the app reads at startup: where files come from (source root),
where they go (target root), and the list of category folders.
"""

SOURCE_ROOT = "D:\\安法\\project\\mock-data-source"
TARGET_ROOT = "D:\\安法\\project\\mock-data-target"

# If this is empty, the program will transfer every folder in FOLDER_NAMES.
# If only want to test one folder, put the folder name here, for example:
# SELECTED_FOLDER = "體組成"
SELECTED_FOLDER = ""

CATEGORY = [
    "體組成",
    "檢驗紀錄",
    "醫院光學影像",
    "會診記錄",
    "外院資料",
    "過敏報告",
    "看診紀錄",
    "其他",
    "營養衛教",
]
