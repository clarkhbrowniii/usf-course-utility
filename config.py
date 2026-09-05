"""Workstation settings. Use absolute paths or set the matching environment variables."""
import os

ORACLE_SQL_DEVELOPER_PATH = os.environ.get("ORACLE_SQL_DEVELOPER_PATH", "")
DBEAVER_PATH = os.environ.get("DBEAVER_PATH", "")
# An executable, local document, HTML file, or resource directory.
ISM6346_COURSE_PATH = os.environ.get("ISM6346_COURSE_PATH", "")
