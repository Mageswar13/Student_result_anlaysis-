"""Application and database configuration.

Values can be overridden with environment variables so that no password
has to be hard-coded:

    set DB_PASSWORD=your_password        (Windows)
    export DB_PASSWORD=your_password     (Linux / macOS)
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 3306)),
        "user": os.environ.get("DB_USER", "Final_project"),
        "password": os.environ.get("DB_PASSWORD", "R.mageswar@"),
        "database": os.environ.get("DB_NAME", "student_result_db"),
    }

    # A subject is passed when marks >= PASS_PERCENT % of its maximum marks.
    # A student passes only if every subject is passed.
    PASS_PERCENT = 40

    CHART_DIR = os.path.join(BASE_DIR, "static", "charts")
