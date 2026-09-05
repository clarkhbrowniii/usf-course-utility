"""Windows launchers for Business Data Foundations for AI."""
import os

# These workstation paths are used directly, independently of config.py.

SQL_DEVELOPER_PATH = r"C:\Users\chbro\Documents\Education\Programs\MS-AIBEI\ISM 6417\sqldeveloper\sqldeveloper.exe"

SQL_DBEAVER_PATH = r"C:\Users\chbro\AppData\Local\DBeaver\dbeaver.exe"

class ISM6417Course:
    """Return status messages; Windows errors propagate to the route handler."""

    def launch_oracle_sql_developer(self):
        """Open SQL Developer; database connections are configured in that app."""
        os.startfile(SQL_DEVELOPER_PATH)
        return "success", "Oracle SQL Developer launched."

    def launch_dbeaver(self):
        """Ask Windows to launch DBeaver without waiting for it to exit."""
        os.startfile(SQL_DBEAVER_PATH)
        return "success", "DBeaver launched."
