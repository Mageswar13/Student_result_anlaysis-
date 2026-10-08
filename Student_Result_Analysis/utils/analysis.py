"""Pandas / Matplotlib analysis for student results."""
import os
import time

import matplotlib

matplotlib.use("Agg")  # headless backend: render straight to PNG files
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config import Config  # noqa: E402
from utils.db import fetch_all  # noqa: E402

# 8 edges -> 7 grade bands (left-closed):
# [0,40) F, [40,50) D, [50,60) C, [60,70) B, [70,80) B+, [80,90) A, [90,100] A+
GRADE_BINS = [0, 40, 50, 60, 70, 80, 90, 100.01]
GRADE_LABELS = ["F", "D", "C", "B", "B+", "A", "A+"]

MARK_COLUMNS = [
    "student_id", "roll_no", "name", "department",
    "subject", "max_marks", "marks",
]


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_marks_df():
    """Return one row per (student, subject) mark as a DataFrame."""
    rows = fetch_all(
        """
        SELECT s.student_id, s.roll_no, s.name, s.department,
               sub.name AS subject, sub.max_marks, m.marks
        FROM marks m
        JOIN students s   ON s.student_id = m.student_id
        JOIN subjects sub ON sub.subject_id = m.subject_id
        ORDER BY s.roll_no, sub.name
        """
    )
    df = pd.DataFrame(rows, columns=MARK_COLUMNS)
    for col in ("max_marks", "marks"):
        df[col] = pd.to_numeric(df[col])  # DECIMAL arrives as Decimal objects
    return df


# --------------------------------------------------------------------------
# Calculations
# --------------------------------------------------------------------------
def calculate_results(df=None):
    """Build the result sheet: one row per student with totals, %, grade, rank.

    Returns (results_df, subject_names).
    """
    if df is None:
        df = load_marks_df()
    if df.empty:
        return pd.DataFrame(), []

    df = df.copy()
    df["passed"] = df["marks"] >= df["max_marks"] * Config.PASS_PERCENT / 100

    pivot = df.pivot_table(
        index=["student_id", "roll_no", "name", "department"],
        columns="subject",
        values="marks",
        aggfunc="first",
    )
    subjects = list(pivot.columns)

    agg = df.groupby("student_id").agg(
        total=("marks", "sum"),
        max_total=("max_marks", "sum"),
        all_passed=("passed", "all"),
    )

    res = pivot.reset_index().merge(agg, on="student_id")
    res["percentage"] = (res["total"] / res["max_total"] * 100).round(2)
    res["grade"] = pd.cut(
        res["percentage"],
        bins=GRADE_BINS,
        labels=GRADE_LABELS,
        right=False,
        include_lowest=True,
    ).astype(str)
    res["result"] = np.where(res["all_passed"], "Pass", "Fail")
    res["rank"] = res["total"].rank(ascending=False, method="min").astype(int)

    res = res.sort_values(["rank", "roll_no"]).reset_index(drop=True)
    return res, subjects


def get_summary(results=None, subjects=None, df=None):
    """Headline numbers for the dashboard and analysis page."""
    if results is None:
        df = load_marks_df() if df is None else df
        results, subjects = calculate_results(df)

    if results.empty:
        return {
            "has_data": False, "total_students": 0, "pass_count": 0,
            "fail_count": 0, "pass_percentage": 0.0, "class_average": 0.0,
            "highest": 0.0, "lowest": 0.0, "topper": None, "toppers": [],
            "subject_stats": [],
        }

    pass_count = int((results["result"] == "Pass").sum())
    total_students = int(len(results))

    top_total = results["total"].max()
    toppers = results[results["total"] == top_total]

    subject_stats = []
    for sub in subjects:
        col = results[sub].dropna()
        if col.empty:
            continue
        subject_stats.append({
            "subject": sub,
            "average": round(float(col.mean()), 2),
            "highest": float(col.max()),
            "lowest": float(col.min()),
            "appeared": int(col.count()),
        })

    return {
        "has_data": True,
        "total_students": total_students,
        "pass_count": pass_count,
        "fail_count": total_students - pass_count,
        "pass_percentage": round(pass_count / total_students * 100, 2),
        "class_average": round(float(results["percentage"].mean()), 2),
        "highest": float(results["percentage"].max()),
        "lowest": float(results["percentage"].min()),
        "topper": toppers.iloc[0].to_dict(),
        "toppers": toppers[["roll_no", "name", "total", "percentage"]]
        .to_dict("records"),
        "subject_stats": subject_stats,
    }


def results_for_display(results):
    """Convert a results DataFrame to a list of dicts; NaN becomes None."""
    if results.empty:
        return []
    clean = results.astype(object).where(results.notna(), None)
    return clean.to_dict("records")


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def _save(fig, filename):
    os.makedirs(Config.CHART_DIR, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(Config.CHART_DIR, filename), dpi=110)
    plt.close(fig)


def _empty_chart(filename, title):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.text(0.5, 0.5, "No data available", ha="center", va="center",
            fontsize=13, color="gray")
    ax.set_title(title)
    ax.axis("off")
    _save(fig, filename)


def generate_charts(results=None, subjects=None):
    """Create all analysis charts as PNGs in static/charts/.

    Each chart is wrapped in its own try/except so one failure does not
    stop the others. Returns a dict {chart_key: filename}.
    """
    if results is None:
        results, subjects = calculate_results()

    charts = {
        "subject_avg": "subject_avg.png",
        "top_students": "top_students.png",
        "pass_fail": "pass_fail.png",
        "grades": "grades.png",
    }

    if results.empty:
        for key, fname in charts.items():
            _empty_chart(fname, key.replace("_", " ").title())
        return charts

    # 1. Average marks by subject
    try:
        avgs = results[subjects].mean().round(2)
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(avgs.index, avgs.values, color="#4f46e5")
        ax.bar_label(bars, fmt="%.1f", padding=2)
        ax.set_title("Average Marks by Subject")
        ax.set_ylabel("Average marks")
        ax.set_ylim(0, max(100, avgs.max() * 1.1))
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
        _save(fig, charts["subject_avg"])
    except Exception:
        _empty_chart(charts["subject_avg"], "Average Marks by Subject")

    # 2. Top 5 students by percentage
    try:
        top = results.nsmallest(5, "rank").iloc[::-1]
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.barh(top["name"], top["percentage"], color="#059669")
        ax.bar_label(bars, fmt="%.1f%%", padding=3)
        ax.set_title("Top 5 Students")
        ax.set_xlabel("Percentage")
        ax.set_xlim(0, 110)
        _save(fig, charts["top_students"])
    except Exception:
        _empty_chart(charts["top_students"], "Top 5 Students")

    # 3. Pass vs Fail
    try:
        passed = int((results["result"] == "Pass").sum())
        failed = int(len(results)) - passed
        values = [v for v in (passed, failed) if v > 0]
        labels = [l for l, v in (("Pass", passed), ("Fail", failed)) if v > 0]
        colors = [c for c, v in (("#16a34a", passed), ("#dc2626", failed))
                  if v > 0]
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%",
               startangle=90, wedgeprops={"edgecolor": "white"})
        ax.set_title("Pass vs Fail")
        _save(fig, charts["pass_fail"])
    except Exception:
        _empty_chart(charts["pass_fail"], "Pass vs Fail")

    # 4. Grade distribution
    try:
        dist = (results["grade"].value_counts()
                .reindex(GRADE_LABELS[::-1], fill_value=0))
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(dist.index, dist.values, color="#f59e0b")
        ax.bar_label(bars, padding=2)
        ax.set_title("Grade Distribution")
        ax.set_xlabel("Grade")
        ax.set_ylabel("Students")
        ax.yaxis.get_major_locator().set_params(integer=True)
        _save(fig, charts["grades"])
    except Exception:
        _empty_chart(charts["grades"], "Grade Distribution")

    return charts


def chart_version():
    """Timestamp used to bust the browser cache after charts are redrawn."""
    return int(time.time())
