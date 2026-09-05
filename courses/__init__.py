"""Shared local launch helpers; course-specific behavior lives in each package."""
import os
from pathlib import Path
import subprocess

from flask import current_app


def launch_path(setting, label, *, resource=False):
    configured = current_app.config.get(setting)
    if not configured or not str(configured).strip():
        current_app.logger.warning("%s is not configured", setting)
        return "warning", f"{label} path is not configured."
    try:
        path = Path(configured).expanduser()
        if not path.is_absolute() or not path.exists():
            current_app.logger.warning("Invalid %s: %s", setting, path)
            return "error", f"{label} path does not exist or is not absolute. Check {setting} in config.py."
        if not resource and (not path.is_file() or path.suffix.lower() != ".exe"):
            current_app.logger.warning("%s must point to an executable: %s", setting, path)
            return "error", f"{label} path must point to an .exe file."
        if resource and path.suffix.lower() != ".exe":
            os.startfile(str(path))
        else:
            subprocess.Popen([str(path)], cwd=str(path.parent), shell=False)
        current_app.logger.info("Launch requested for %s", label)
        return "success", f"{label} launched."
    except FileNotFoundError:
        current_app.logger.exception("Launch target disappeared: %s", setting)
        return "error", f"{label} could not be found. Check its configured path."
    except Exception:
        current_app.logger.exception("Unable to launch %s", label)
        return "error", f"{label} could not be launched. See instance/utility.log for details."
