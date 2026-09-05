"""Local course navigation and action dispatch. Run with python app.py."""
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import secrets

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import SecurityError

from courses.ism6346.actions import launch_course_experience, update_course_experience
from courses.ism6417.actions import launch_dbeaver, launch_oracle_sql_developer

ACTION_HANDLERS = {
    "ism6346": {"update": update_course_experience, "launch": launch_course_experience},
    "ism6417": {"oracle": launch_oracle_sql_developer, "dbeaver": launch_dbeaver},
}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config")
    app.config.update(SECRET_KEY=secrets.token_hex(32), SESSION_COOKIE_SAMESITE="Strict",
                      MAX_CONTENT_LENGTH=16 * 1024, TRUSTED_HOSTS=["127.0.0.1", "localhost", "[::1]"])
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(exist_ok=True)
    log_path = Path(app.instance_path) / "utility.log"
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
        if "action_token" not in session:
            session["action_token"] = secrets.token_hex(32)
        image_name = "usf-splash.webp" if (Path(app.static_folder) / "images/usf-splash.webp").exists() else "usf-splash.png"
        return {"action_token": session["action_token"], "splash_image": image_name}

    def get_course(course_code):
        course = courses.get(course_code)
        if not course or not course["enabled"]:
            abort(404)
        return course

    @app.get("/")
    def home():
        return render_template("home.html", courses=[c for c in courses.values() if c["enabled"]])

    @app.get("/course/<course_code>")
    def course_page(course_code):
        return render_template("course.html", course=get_course(course_code))

    @app.post("/course/<course_code>/action/<action_id>")
    def run_action(course_code, action_id):
        get_course(course_code)
        handler = ACTION_HANDLERS.get(course_code, {}).get(action_id)
        if handler is None:
            abort(404)
        token = session.get("action_token", "")
        if not token or not secrets.compare_digest(token, request.form.get("action_token", "")):
            abort(400, description="This action form expired. Return to the course and try again.")
        app.logger.info("Action invoked: %s/%s", course_code, action_id)
        try:
            category, message = handler()
        except Exception:
            app.logger.exception("Unexpected action failure: %s/%s", course_code, action_id)
            category, message = "error", "The action could not be completed. See instance/utility.log for details."
        flash(message, category)
        return redirect(url_for("course_page", course_code=course_code), code=303)

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def error_page(error):
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
