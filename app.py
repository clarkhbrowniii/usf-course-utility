"""Local course navigation and action dispatch. Run with python app.py."""
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import secrets

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import SecurityError

from courses import ism6417, ism6346
from courses.ism6346.actions import ISM6346Course
from courses.ism6417.actions import ISM6417Course

def create_app(test_config=None):
    """Build the local app, course handlers, and explicit action routes."""
    app = Flask(__name__, instance_relative_config=True)
    ism6346 = ISM6346Course()
    ism6417 = ISM6417Course()
    app.config.from_object("config")
    # Restarting invalidates old sessions; ZIP uploads are capped at 100 MiB.
    app.config.update(SECRET_KEY=secrets.token_hex(32), SESSION_COOKIE_SAMESITE="Strict",
                      MAX_CONTENT_LENGTH=100 * 1024 * 1024, TRUSTED_HOSTS=["127.0.0.1", "localhost", "[::1]"])
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(exist_ok=True)
    log_path = Path(app.instance_path) / "utility.log"
    # Repeated factory calls share the logger; avoid duplicate file handlers.
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == str(log_path)
               for h in app.logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    with (Path(app.root_path) / "data/courses.json").open(encoding="utf-8") as source:
        courses = json.load(source)

    @app.context_processor
    def shell_context():
        """Supply every template with a session form token and splash image."""
        if "action_token" not in session:
            session["action_token"] = secrets.token_hex(32)
        image_name = "usf-splash.webp" if (Path(app.static_folder) / "images/usf-splash.webp").exists() else "usf-splash.png" #type: ignore
        return {"action_token": session["action_token"], "splash_image": image_name}

    def get_course(course_code):
        """Reject unknown or disabled courses for both views and actions."""
        course = courses.get(course_code)
        if not course or not course["enabled"]:
            abort(404)
        return course

    @app.get("/")
    def home():
        """List enabled courses from data/courses.json."""
        return render_template("home.html", courses=[c for c in courses.values() if c["enabled"]])

    @app.get("/course/<course_code>")
    def course_page(course_code):
        """Render one course using shared action-card markup."""
        return render_template("course.html", course=get_course(course_code))

    def run_course_action(course_code, handler):
        """Shared form validation, status reporting, and return navigation."""
        get_course(course_code)
        token = session.get("action_token", "")
        # Validate before running handlers that launch programs or replace files.
        if not token or not secrets.compare_digest(token, request.form.get("action_token", "")):
            abort(400, description="This action form expired. Return to the course and try again.")
        app.logger.info("Action invoked: %s", request.path)
        try:
            category, message = handler()
        except Exception:
            app.logger.exception("Unexpected action failure: %s", request.path)
            category, message = "error", "The action could not be completed. See instance/utility.log for details."
        flash(message, category)
        # HTTP 303 prevents refresh from repeating the action's POST request.
        return redirect(url_for("course_page", course_code=course_code), code=303)

    @app.post("/course/ism6346/update")
    def update_ism6346():
        """Forward the ZIP; the lambda defers work until validation passes."""
        course_zip = request.files.get("course_zip")

        return run_course_action(
            "ism6346",
            lambda: ism6346.update_course_experience(course_zip)
        )

    @app.post("/course/ism6346/launch")
    def launch_ism6346():
        """Start the course server and open its student page."""
        return run_course_action("ism6346", ism6346.launch_course_experience)

    @app.post("/course/ism6417/oracle")
    def launch_ism6417_oracle():
        """Open Oracle SQL Developer on this workstation."""
        return run_course_action("ism6417",ism6417.launch_oracle_sql_developer)

    @app.post("/course/ism6417/dbeaver")
    def launch_ism6417_dbeaver():
        """Open DBeaver on this workstation."""
        return run_course_action("ism6417", ism6417.launch_dbeaver)

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def error_page(error):
        """Render friendly errors without exposing tracebacks in the page."""
        # Host rejection happens before Flask can build template URLs.
        if isinstance(error, SecurityError):
            return "Open USF Course Utility at http://127.0.0.1:5000.", 400
        message = {400: "The request could not be completed. Reload the course page and try again.",
                   404: "This course or action could not be found.",
                   500: "Something went wrong. See instance/utility.log for details."}[error.code]
        return render_template("error.html", message=message, error_code=error.code), error.code

    app.logger.info("USF Course Utility started")
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
