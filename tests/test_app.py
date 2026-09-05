"""Route and course-action checks with temporary files and mocked desktop launches."""
import io
import json
import zipfile
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from courses import launch_path
from courses.ism6346.actions import ISM6346Course


class UtilityTests(unittest.TestCase):
    def setUp(self):
        # Load a page first to establish the same session token used by real forms.
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-only",
                               "ORACLE_SQL_DEVELOPER_PATH": "", "DBEAVER_PATH": "",
                               "ISM6346_COURSE_PATH": ""})
        self.client = self.app.test_client()
        self.client.get("/")
        with self.client.session_transaction() as session:
            self.token = session["action_token"]

    def post_action(self, course, action):
        return self.client.post(f"/course/{course}/{action}",
                                data={"action_token": self.token}, follow_redirects=True)

    def test_navigation(self):
        metadata = json.loads((Path(self.app.root_path) / "data/courses.json").read_text())
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertEqual(len(metadata), 10)
        for course in metadata.values():
            self.assertIn(course["title"], home.text)
            page = self.client.get(f'/course/{course["id"]}')
            self.assertEqual(page.status_code, 200)
            self.assertIn(course["title"], page.text)
            self.assertIn('href="/"', page.text)
            for action in course["actions"]:
                self.assertIn(f'action="/course/{course["id"]}/{action["id"]}"', page.text)
            if not course["actions"]:
                self.assertIn("Course utilities have not yet been configured.", page.text)
        self.assertEqual(self.client.get("/course/unknown").status_code, 404)
        response = self.client.get("/static/images/usf-splash.png")
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_placeholder_and_missing_paths(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ISM6346Course, "COURSE_DIR", directory):
            result = self.post_action("ism6346", "launch")
            self.assertIn("Course experience files could not be found.", result.text)
        self.assertIn("No course update was selected.", self.post_action("ism6346", "update").text)

    def test_action_protection(self):
        for route in ("/course/ism6346/update", "/course/ism6346/launch",
                      "/course/ism6417/oracle", "/course/ism6417/dbeaver"):
            self.assertEqual(self.client.get(route).status_code, 405)
            self.assertEqual(self.client.post(route).status_code, 400)
        self.assertEqual(self.client.post("/course/ism6417/unknown").status_code, 404)
        self.assertEqual(self.client.post("/course/ism6417/action/dbeaver").status_code, 404)
        self.assertEqual(self.client.get("/", headers={"Host": "untrusted.example"}).status_code, 400)

    def test_launch_validation_and_os_errors(self):
        with tempfile.TemporaryDirectory() as directory, self.app.app_context():
            executable = Path(directory) / "tool with spaces.exe"
            self.app.config["DBEAVER_PATH"] = str(executable)
            with patch("courses.subprocess.Popen") as popen:
                self.assertEqual(launch_path("DBEAVER_PATH", "DBeaver")[0], "error")
                popen.assert_not_called()
                executable.touch()
                self.assertEqual(launch_path("DBEAVER_PATH", "DBeaver")[0], "success")
                popen.assert_called_once_with([str(executable)], cwd=str(executable.parent), shell=False)
            for error in (FileNotFoundError("missing"), PermissionError("denied"), OSError("invalid")):
                with patch("courses.subprocess.Popen", side_effect=error):
                    self.assertEqual(launch_path("DBEAVER_PATH", "DBeaver")[0], "error")
            self.app.config["DBEAVER_PATH"] = directory
            self.assertEqual(launch_path("DBEAVER_PATH", "DBeaver")[0], "error")

    def test_course_resource_launch(self):
        # Never start a real server or browser during the test run.
        with tempfile.TemporaryDirectory() as directory, patch.object(ISM6346Course, "COURSE_DIR", directory):
            student_files = Path(directory) / "dt6000-student-files"
            student_files.mkdir()
            with patch("courses.ism6346.actions.subprocess.Popen") as popen, \
                    patch("courses.ism6346.actions.time.sleep"), \
                    patch("courses.ism6346.actions.webbrowser.open") as browser:
                self.assertEqual(ISM6346Course().launch_course_experience()[0], "success")
                self.assertEqual(popen.call_args.kwargs["cwd"], student_files)
                self.assertEqual(popen.call_args.args[0][1:], ["-m", "http.server", "8000"])
                browser.assert_called_once_with(ISM6346Course.COURSE_URL)

    def test_explicit_action_routes(self):
        cases = [("ism6346", "update", "app.ISM6346Course.update_course_experience"),
                 ("ism6346", "launch", "app.ISM6346Course.launch_course_experience"),
                 ("ism6417", "oracle", "app.ISM6417Course.launch_oracle_sql_developer"),
                 ("ism6417", "dbeaver", "app.ISM6417Course.launch_dbeaver")]
        for course, action, target in cases:
            with self.subTest(action=action), patch(target, return_value=("success", "Action completed.")) as handler:
                response = self.client.post(f"/course/{course}/{action}",
                                            data={"action_token": self.token})
                handler.assert_called_once_with(*([None] if action == "update" else []))
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["Location"], f"/course/{course}")
                self.assertIn("Action completed.", self.client.get(response.headers["Location"]).text)

    def test_action_failure_redirects_with_message(self):
        with patch("app.ISM6346Course.update_course_experience", side_effect=OSError("failed")):
            response = self.post_action("ism6346", "update")
            self.assertEqual(response.status_code, 200)
            self.assertIn("The action could not be completed.", response.text)

    def test_database_launchers(self):
        # Windows accepts the launch request; application readiness is not checked.
        from courses.ism6417.actions import SQL_DEVELOPER_PATH, SQL_DBEAVER_PATH
        for action, path in (("oracle", SQL_DEVELOPER_PATH), ("dbeaver", SQL_DBEAVER_PATH)):
            with patch("courses.ism6417.actions.os.startfile") as startfile:
                self.assertIn("launched.", self.post_action("ism6417", action).text)
                startfile.assert_called_once_with(path)

    def test_course_zip_upload(self):
        # Limit all replacement writes to a disposable course installation.
        with tempfile.TemporaryDirectory() as directory, patch.object(ISM6346Course, "COURSE_DIR", directory):
            destination = Path(directory) / "dt6000-student-files"
            destination.mkdir()
            original = destination / "old.txt"
            original.write_text("old content")
            invalid = self.client.post("/course/ism6346/update", data={
                "action_token": self.token, "course_zip": (io.BytesIO(b"invalid"), "bad.zip")
            }, follow_redirects=True)
            self.assertIn("not a valid ZIP archive", invalid.text)
            self.assertTrue(original.exists())
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("courses/lesson.txt", "lesson")
                output.writestr("student-engine/index.html", "course")
                output.writestr("config.js", "config")
            archive.seek(0)
            response = self.client.post("/course/ism6346/update", data={
                "action_token": self.token, "course_zip": (archive, "update.zip")
            }, follow_redirects=True)
            self.assertIn("updated successfully", response.text)
            self.assertFalse(original.exists())
            self.assertEqual((destination / "courses/lesson.txt").read_text(), "lesson")


if __name__ == "__main__":
    unittest.main()
