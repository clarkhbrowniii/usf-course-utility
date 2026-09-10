"""Launch the provider-maintained course experience."""
from courses import launch_path


class ISM6346Course:
    """Course actions returning (status category, user message)."""

    def launch_course_experience(self):
        """Open the configured student URL through the shared launcher."""
        return launch_path(
            "ISM6346_COURSE_TARGET", "ISM 6346 course experience", resource=True
        )
