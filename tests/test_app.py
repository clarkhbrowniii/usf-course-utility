import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from courses.ism6417.actions import launch_dbeaver
from courses.ism6346.actions import launch_course_experience


class UtilityTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-only",
                               "ORACLE_SQL_DEVELOPER_PATH": "", "DBEAVER_PATH": "",
                               "ISM6346_COURSE_PATH": ""})
        self.client = self.app.test_client()
        self.client.get("/")
        with self.client.session_transaction() as session:
            self.token = session["action_token"]

    def post_action(self, course, action):
        return self.client.post(f"/course/{course}/action/{action}",
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
            if not course["actions"]:
                self.assertIn("Course utilities have not yet been configured.", page.text)
        self.assertEqual(self.client.get("/course/unknown").status_code, 404)
        response = self.client.get("/static/images/usf-splash.png")
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_placeholder_and_missing_paths(self):
        cases = [("ism6346", "update", "No files were changed."),
                 ("ism6346", "launch", "Course experience path is not configured."),
                 ("ism6417", "oracle", "Oracle SQL Developer path is not configured."),
                 ("ism6417", "dbeaver", "DBeaver path is not configured.")]
        for course, action, message in cases:
            result = self.post_action(course, action)
            self.assertEqual(result.status_code, 200)
            self.assertIn(message, result.text)

    def test_action_protection(self):
        route = "/course/ism6417/action/dbeaver"
        self.assertEqual(self.client.get(route).status_code, 405)
        self.assertEqual(self.client.post(route).status_code, 400)
        self.assertEqual(self.client.post("/course/ism6417/action/unknown").status_code, 404)
        self.assertEqual(self.client.get("/", headers={"Host": "untrusted.example"}).status_code, 400)

    def test_launch_validation_and_os_errors(self):
        with tempfile.TemporaryDirectory() as directory, self.app.app_context():
            executable = Path(directory) / "tool with spaces.exe"
            self.app.config["DBEAVER_PATH"] = str(executable)
            with patch("courses.subprocess.Popen") as popen:
                self.assertEqual(launch_dbeaver()[0], "error")
                popen.assert_not_called()
                executable.touch()
                self.assertEqual(launch_dbeaver()[0], "success")
                popen.assert_called_once_with([str(executable)], cwd=str(executable.parent), shell=False)
            for error in (FileNotFoundError("missing"), PermissionError("denied"), OSError("invalid")):
                with patch("courses.subprocess.Popen", side_effect=error):
                    self.assertEqual(launch_dbeaver()[0], "error")
            self.app.config["DBEAVER_PATH"] = directory
            self.assertEqual(launch_dbeaver()[0], "error")

    def test_course_resource_launch(self):
        with tempfile.TemporaryDirectory() as directory, self.app.app_context():
            self.app.config["ISM6346_COURSE_PATH"] = directory
            with patch("courses.os.startfile", create=True) as startfile:
                self.assertEqual(launch_course_experience()[0], "success")
                startfile.assert_called_once_with(directory)


if __name__ == "__main__":
    unittest.main()
