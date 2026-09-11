"""Route and course-action checks with temporary files and mocked desktop launches."""
import json
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
                               "ISM6346_COURSE_TARGET": ""})
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

    def test_missing_course_target(self):
        result = self.post_action("ism6346", "launch")
        self.assertIn("ISM 6346 course experience path is not configured.", result.text)
    def test_action_protection(self):
        for route in ("/course/ism6346/launch",
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
        # URL launches do not require a local installation or start a server.
        with self.app.app_context():
            for scheme in ("http", "https"):
                url = f"{scheme}://example.com/student-engine/?course=ISM6346&week=home"
                with self.subTest(scheme=scheme), patch.dict(self.app.config, {
                    "ISM6346_COURSE_TARGET": url
                }), patch("courses.subprocess.Popen") as popen, \
                        patch("courses.webbrowser.open") as browser:
                    self.assertEqual(ISM6346Course().launch_course_experience(),
                                     ("success", "ISM 6346 course experience launched."))
                    popen.assert_not_called()
                    browser.assert_called_once_with(url)

    def test_explicit_action_routes(self):
        cases = [("ism6346", "launch", "app.ISM6346Course.launch_course_experience"),
                 ("ism6417", "oracle", "app.ISM6417Course.launch_oracle_sql_developer"),
                 ("ism6417", "dbeaver", "app.ISM6417Course.launch_dbeaver")]
        for course, action, target in cases:
            with self.subTest(action=action), patch(target, return_value=("success", "Action completed.")) as handler:
                response = self.client.post(f"/course/{course}/{action}",
                                            data={"action_token": self.token})
                handler.assert_called_once_with()
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["Location"], f"/course/{course}")
                self.assertIn("Action completed.", self.client.get(response.headers["Location"]).text)

    def test_action_failure_redirects_with_message(self):
        with patch("app.ISM6346Course.launch_course_experience", side_effect=OSError("failed")):
            response = self.post_action("ism6346", "launch")
            self.assertEqual(response.status_code, 200)
            self.assertIn("The action could not be completed.", response.text)

    def test_database_launchers(self):
        # Windows accepts the launch request; application readiness is not checked.
        oracle = self.app.config["ISM6417_ORACLE_TARGET"]
        dbeaver = self.app.config["ISM6417_DBEAVER_TARGET"]
        for action, path in (("oracle", oracle), ("dbeaver", dbeaver)):
            with patch("courses.ism6417.actions.os.startfile") as startfile:
                self.assertIn("launched.", self.post_action("ism6417", action).text)
                startfile.assert_called_once_with(path)

    def test_course_update_removed(self):
        page = self.client.get("/course/ism6346")
        self.assertNotIn("Update Course Experience", page.text)
        self.assertNotIn('type="file"', page.text)
        self.assertIn("Launch Course Experience", page.text)
        self.assertIn("Open Course Folder", page.text)
        self.assertIn("2 configured", page.text)
        self.assertEqual(self.client.get("/course/ism6346/update").status_code, 404)
        self.assertEqual(self.post_action("ism6346", "update").status_code, 404)

if __name__ == "__main__":
    unittest.main()
