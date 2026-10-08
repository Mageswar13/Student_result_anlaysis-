"""Student Result Analysis - main Flask application."""
from flask import Flask, redirect, render_template, request, url_for
from mysql.connector import Error as MySQLError
from mysql.connector import IntegrityError

from config import Config
from utils import analysis
from utils.db import execute, fetch_all, fetch_one

app = Flask(__name__)
app.config.from_object(Config)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def message_page(message, status="success", back_url=None, back_text="Back",
                 code=200):
    """Render the shared success / error page."""
    return render_template(
        "success.html",
        message=message,
        status=status,
        back_url=back_url or url_for("index"),
        back_text=back_text,
    ), code


def get_students():
    return fetch_all(
        "SELECT student_id, roll_no, name, department, year "
        "FROM students ORDER BY roll_no"
    )


def get_subjects():
    return fetch_all(
        "SELECT subject_id, name, max_marks FROM subjects ORDER BY name"
    )


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    counts = fetch_one(
        "SELECT (SELECT COUNT(*) FROM students) AS students, "
        "       (SELECT COUNT(*) FROM subjects) AS subjects, "
        "       (SELECT COUNT(*) FROM marks)    AS marks"
    )
    summary = analysis.get_summary()
    return render_template("index.html", counts=counts, summary=summary)


@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "GET":
        return render_template("add_student.html", form={})

    form = {k: request.form.get(k, "").strip() for k in
            ("roll_no", "name", "email", "department", "year")}

    errors = []
    if not form["roll_no"]:
        errors.append("Roll number is required.")
    if not form["name"]:
        errors.append("Name is required.")
    if not form["department"]:
        errors.append("Department is required.")
    if not form["year"].isdigit() or not 1 <= int(form["year"]) <= 6:
        errors.append("Year must be a number between 1 and 6.")
    if errors:
        return render_template("add_student.html", form=form,
                               errors=errors), 400

    try:
        execute(
            "INSERT INTO students (roll_no, name, email, department, year) "
            "VALUES (%s, %s, %s, %s, %s)",
            (form["roll_no"], form["name"], form["email"] or None,
             form["department"], int(form["year"])),
        )
    except IntegrityError:
        return render_template(
            "add_student.html", form=form,
            errors=["A student with this roll number or email already "
                    "exists."],
        ), 409

    return message_page(
        f"Student {form['name']} ({form['roll_no']}) added successfully.",
        back_url=url_for("add_marks"), back_text="Add marks now",
    )


@app.route("/add_marks", methods=["GET", "POST"])
def add_marks():
    students = get_students()
    subjects = get_subjects()

    if request.method == "GET":
        return render_template("add_marks.html", students=students,
                               subjects=subjects, form={})

    form = {k: request.form.get(k, "").strip() for k in
            ("student_id", "subject_id", "marks")}

    def fail(msg, code=400):
        return render_template("add_marks.html", students=students,
                               subjects=subjects, form=form,
                               errors=[msg]), code

    if not form["student_id"].isdigit() or not form["subject_id"].isdigit():
        return fail("Please select a student and a subject.")

    try:
        marks = float(form["marks"])
    except ValueError:
        return fail("Marks must be a number.")

    subject = fetch_one(
        "SELECT name, max_marks FROM subjects WHERE subject_id = %s",
        (int(form["subject_id"]),),
    )
    student = fetch_one(
        "SELECT name FROM students WHERE student_id = %s",
        (int(form["student_id"]),),
    )
    if not subject or not student:
        return fail("Selected student or subject does not exist.")
    if not 0 <= marks <= subject["max_marks"]:
        return fail(f"Marks must be between 0 and {subject['max_marks']} "
                    f"for {subject['name']}.")

    # one mark per student per subject: re-entering simply updates it
    execute(
        "INSERT INTO marks (student_id, subject_id, marks) "
        "VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE marks = VALUES(marks)",
        (int(form["student_id"]), int(form["subject_id"]), marks),
    )
    return message_page(
        f"Saved {marks:g} / {subject['max_marks']} in {subject['name']} "
        f"for {student['name']}.",
        back_url=url_for("add_marks"), back_text="Add more marks",
    )


@app.route("/view_results")
def view_results():
    results, subjects = analysis.calculate_results()
    return render_template(
        "view_results.html",
        rows=analysis.results_for_display(results),
        subjects=subjects,
    )


@app.route("/analysis")
def analysis_page():
    results, subjects = analysis.calculate_results()
    charts = analysis.generate_charts(results, subjects)
    summary = analysis.get_summary(results, subjects)
    return render_template(
        "analysis.html",
        summary=summary,
        charts=charts,
        version=analysis.chart_version(),
    )


@app.route("/delete_student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    execute("DELETE FROM students WHERE student_id = %s", (student_id,))
    return redirect(url_for("view_results"))


# --------------------------------------------------------------------------
# Error handling
# --------------------------------------------------------------------------
@app.errorhandler(MySQLError)
def handle_db_error(err):
    return message_page(
        "Database error: " + str(err) + ". Check config.py and make sure "
        "MySQL is running and schema.sql has been executed.",
        status="error", code=500,
    )


@app.errorhandler(404)
def handle_404(_err):
    return message_page("Page not found.", status="error", code=404)


if __name__ == "__main__":
    app.run(debug=True)
