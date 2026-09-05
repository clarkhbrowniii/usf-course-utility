# USF Course Utility

A local desktop-style launcher for the USF **MS in AI in Business & Enterprise Integration** program. Uses Python, Flask, Jinja2, Bootstrap 5, Bootstrap Icons, custom CSS, and minimal JavaScript. No database or frontend build system.

## Setup and run

Requires Windows and Python 3.10+. Bootstrap and icons load via CDN and require internet access.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. Stop with Ctrl+C. If activation is restricted, use `.venv\Scripts\python -m pip install -r requirements.txt` and `.venv\Scripts\python app.py` directly. In Command Prompt, activate with `.venv\Scripts\activate.bat`.

The server binds to loopback with debug disabled. Keep it local: actions open applications on the machine running Flask. Launch forms use POST and a session token. Reload open forms after restarting the server.

## Configuration

Current course actions use workstation paths in their `actions.py` modules. For ISM 6346, edit `ISM6346Course.COURSE_DIR` and `COURSE_URL` in `courses/ism6346/actions.py`. For ISM 6417, edit `SQL_DEVELOPER_PATH` and `SQL_DBEAVER_PATH` in `courses/ism6417/actions.py`. Restart after changes.

The optional shared `launch_path` helper uses the following `config.py` settings or matching environment variables. The current course classes do not use this helper.

| Setting | Value |
| --- | --- |
| `ORACLE_SQL_DEVELOPER_PATH` | Absolute path to your Oracle SQL Developer `.exe` |
| `DBEAVER_PATH` | Absolute path to your DBeaver `.exe` |
| `ISM6346_COURSE_PATH` | Absolute path to a course executable, local HTML/document, or directory |

For Oracle SQL Developer, locate its installed executable and assign that full path to `ORACLE_SQL_DEVELOPER_PATH`. For DBeaver, assign its installed executable to `DBEAVER_PATH`. When editing Python directly, use raw strings or forward slashes for Windows paths. Restart after configuration changes.

Database connections are configured inside Oracle SQL Developer and DBeaver. This utility opens those applications; it does not provision or start database servers. Missing paths and failures appear in the course panel and log. Success means Windows accepted the launch request, not that the application or database is ready.

ISM 6346 Update uploads a ZIP through the browser (100 MiB request limit). The archive must contain `courses`, `student-engine`, and `config.js` at its root. The updater replaces the contents of the existing `dt6000-student-files` directory, including local edits, and has no rollback if extraction fails. Launch starts Python's HTTP server on port 8000 and opens `COURSE_URL`. Each launch starts a separate server console; close that console to stop it.

## Structure

```text
app.py                         Flask factory, routes, dispatch, status, logging
config.py                      Workstation paths
requirements.txt               Flask dependency
courses/__init__.py            Shared launch helper
courses/ism6346/actions.py      ZIP upload updater and student-engine launcher
courses/ism6417/actions.py      Oracle and DBeaver launchers
data/courses.json              All ten courses and action UI metadata
templates/base.html            Shared application shell
templates/home.html            Course explorer
templates/course.html          Reusable course view
templates/error.html           Friendly error view
static/css/app.css             USF theme and proportional 60/40 layout
static/js/app.js                Double-submit prevention
static/images/usf-splash.png    Supplied splash artwork
tests/test_app.py              Navigation and launcher checks
instance/utility.log           Runtime log (created automatically; rotates)
```

The supplied PNG is used unchanged. To use the planned WebP asset later, place it at `static/images/usf-splash.webp`; it automatically takes precedence. Both use `object-fit: cover` in the shared panel. The tall source image crops vertically on wide desktop viewports. Theme colors are CSS variables. Desktop columns stay proportional at 60/40; below 761px they stack.

## Add an action or course package

1. Add a function to the course's `actions.py`. Return `(category, message)` using `success`, `warning`, `error`, or `info`. Keep automation here, outside `app.py`.
2. Add an explicit POST route in `app.py`, such as `/course/ism6346/update`. Call `run_course_action(course_code, handler)` to validate the form, run the action, display its result, and redirect to the course page.
3. Add its `id`, `endpoint` (the route function name), `label`, Bootstrap `bi-...` icon, and `description` to the course's `actions` array in `data/courses.json`.
4. Put machine paths in `config.py`. Validate launch targets and log failures.

For another course, create `courses/<course_id>/__init__.py` and `actions.py` only when actual behavior exists, then follow those steps. All ten courses already use the shared template; the other eight show a placeholder and Home navigation. Metadata's `enabled` flag controls navigation and route availability.

## Validation

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Tests cover all course routes, Home links, placeholders, form protection, missing paths, safe launch arguments, Windows resource opening, and OS errors. Launches are mocked so tests do not open programs. Real application launches require your configured installation paths.
