# USF Course Utility

A local desktop-style web utility for managing and launching graduate course resources for the University of South Florida's **MS in AI in Business & Enterprise Integration** program.

The application provides a single browser-based interface for accessing course-specific tools, development environments, databases, and local course experiences.

## Overview

USF Course Utility is intentionally lightweight.

The application runs locally and uses a simple Flask interface inspired by desktop development tools such as Atom. Each graduate course has its own utility page containing actions relevant to that course.

Examples include:

- Launching local course experiences
- Updating course resources
- Launching database development environments
- Opening course-specific tools
- Providing a common interface for future course automation

Course functionality is added incrementally as needed.

## Technology Stack

- Python
- Flask
- Jinja2
- Bootstrap 5
- Bootstrap Icons
- HTML
- CSS
- Minimal JavaScript

The project intentionally avoids unnecessary frontend frameworks, databases, and build systems.

## Courses

The utility supports the following graduate courses:

| Course | Title |
|---|---|
| ISM 6346 | Digital Business Transformation Foundations |
| ISM 6417 | Business Data Foundations for AI |
| ISM 6173 | Agentic AI and Business Process Design |
| ISM 6468 | Applied Machine Learning for Business |
| ISM 6150 | Enterprise Data Analytics |
| ISM 6416 | Building Data Pipelines for AI |
| ISM 6179 | Generative AI and Enterprise Applications |
| ISM 6178 | Enterprise Architecture for Scalable AI Deployment |
| ISM 6576 | AI Security, Privacy, and Governance |
| ISM 6174 | Integrating AI into the Enterprise |

## Initial Course Utilities

### ISM 6346 — Digital Business Transformation Foundations

- Update Course Experience
- Launch Course Experience
- Return Home

### ISM 6417 — Business Data Foundations for AI

- Launch Oracle SQL Developer DB
- Launch DBeaver for PostgreSQL DB
- Return Home

Additional utilities will be implemented as course requirements develop.

## Project Structure

```text
usf-course-utility/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── courses/
│   ├── __init__.py
│   ├── ism6346/
│   │   ├── __init__.py
│   │   └── actions.py
│   └── ism6417/
│       ├── __init__.py
│       └── actions.py
│
├── templates/
│   ├── base.html
│   ├── home.html
│   └── course.html
│
├── static/
│   ├── css/
│   │   └── app.css
│   ├── js/
│   │   └── app.js
│   └── images/
│       └── usf-splash.webp
│
├── data/
│   └── courses.json
│
└── instance/
    └── utility.log
