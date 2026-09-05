from flask import current_app
from courses import launch_path


def update_course_experience():
    """Placeholder: update behavior has not yet been defined."""
    current_app.logger.info("Course update requested; behavior not yet defined")
    return "info", "Course updates have not yet been implemented. No files were changed."


def launch_course_experience():
    return launch_path("ISM6346_COURSE_PATH", "Course experience", resource=True)
