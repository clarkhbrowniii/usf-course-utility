"""Course actions for Digital Business Transformation Foundations."""
import os
import shutil
import zipfile
from pathlib import Path

from flask import current_app

from courses import launch_path


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

    def open_course_folder(self):
        """Open the configured course root in Windows File Explorer."""
        os.startfile(current_app.config["ISM6346_ROOT_DIR"])
        return "success", "ISM 6346 course folder opened."

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

                zip_file.extractall(student_files)

        except zipfile.BadZipFile:
            return "error", "The selected file is not a valid ZIP archive."

        return "success", "ISM 6346 course experience updated successfully."

    def launch_course_experience(self):
        """Open the configured student URL through the shared launcher."""
        return launch_path(
            "ISM6346_COURSE_TARGET", "ISM 6346 course experience", resource=True
        )
