"""Windows launchers for Business Data Foundations for AI."""
import os
from flask import current_app

class ISM6417Course:
    """Return status messages; Windows errors propagate to the route handler."""

    def launch_oracle_sql_developer(self):
        """Open SQL Developer; database connections are configured in that app."""
        os.startfile(current_app.config["ISM6417_ORACLE_TARGET"])
        return "success", "Oracle SQL Developer launched."

    def launch_dbeaver(self):
        """Ask Windows to launch DBeaver without waiting for it to exit."""
        os.startfile(current_app.config["ISM6417_DBEAVER_TARGET"])
        return "success", "DBeaver launched."
