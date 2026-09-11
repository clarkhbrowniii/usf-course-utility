"""Course actions for Digital Business Transformation Foundations."""
import os

from flask import current_app

from courses import launch_path


class ISM6346Course:
    """Workstation-specific actions returning (status category, user message)."""

    def open_course_folder(self):
        """Open the configured course root in Windows File Explorer."""
        os.startfile(current_app.config["ISM6346_ROOT_DIR"])
        return "success", "ISM 6346 course folder opened."

    def launch_course_experience(self):
        """Open the configured student URL through the shared launcher."""
        return launch_path(
            "ISM6346_COURSE_TARGET", "ISM 6346 course experience", resource=True
        )
