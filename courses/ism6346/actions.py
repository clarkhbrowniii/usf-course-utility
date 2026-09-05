"""Install uploaded course content and launch the student engine."""
import shutil
import subprocess
import sys
import time
import webbrowser
import zipfile
from pathlib import Path
from flask import current_app


class ISM6346Course:
    """Workstation-specific actions returning (status category, user message)."""

    COURSE_URL = (
        # The engine reads course version and student identity from this URL.
        "http://localhost:8000/student-engine/"
        "?course=Digital_Transformation_6000"
        "&institution=USF"
        "&version=v1.1"
        "&sid=cbrown"
        "&sname=Clark%20Brown"
    )

    def update_course_experience(self, course_zip):
        """Replace installed content using an uploaded Werkzeug ZIP stream."""
        student_files = Path(current_app.config["ISM6346_COURSE_DIR"]) / "dt6000-student-files"

        if not course_zip or not course_zip.filename:
            return "warning", "No course update was selected."

        try:
            with zipfile.ZipFile(course_zip, "r") as zip_file:

                root_items = {
                    # Assets must be at the ZIP root, not inside a wrapper folder.
                    Path(name).parts[0]
                    for name in zip_file.namelist()
                    if name
                }

                required_items = {
                    "courses",
                    "student-engine",
                    "config.js",
                }

                if not required_items.issubset(root_items):
                    return "error", "The selected ZIP is not a valid ISM 6346 course update."

                # Full replacement removes local edits. Extraction failure after
                # deletion can leave a partial installation; there is no rollback.
                for item in student_files.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()

                # Extract the new course files
                zip_file.extractall(student_files)

        except zipfile.BadZipFile:
            return "error", "The selected file is not a valid ZIP archive."

        return "success", "ISM 6346 course experience updated successfully."

    def launch_course_experience(self):
        """Start a separate HTTP server and open the configured student URL."""
        student_files = Path(current_app.config["ISM6346_COURSE_DIR"]) / "dt6000-student-files"

        if not student_files.exists():
            return "error", "Course experience files could not be found."

        subprocess.Popen(
            # Each launch starts a server; its separate console controls its lifetime.
            [
                sys.executable,
                "-m",
                "http.server",
                "8000",
            ],
            cwd=student_files,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        time.sleep(2)
        # The startup delay above does not verify server readiness.

        webbrowser.open(self.COURSE_URL)

        return "success", "ISM 6346 course experience launched."
