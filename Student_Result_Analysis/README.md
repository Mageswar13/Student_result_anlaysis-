# Student Result Analysis

A Flask web app to register students, enter subject marks, and analyse results
(totals, percentage, grade, rank, topper, pass %, charts).

**Stack:** Flask · MySQL · Pandas / NumPy · Matplotlib

## Setup

1. **Install dependencies**

   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # Linux / macOS
   pip install -r requirements.txt
   ```

2. **Create the database**

   ```bash
   mysql -u root -p < database/schema.sql
   ```

3. **Configure the connection** in `config.py`, or via environment variables
   (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).

4. **Run**

   ```bash
   python app.py
   ```

   Open <http://127.0.0.1:5000>.

## Pages

| URL              | Purpose                                              |
|------------------|------------------------------------------------------|
| `/`              | Dashboard: counts, topper, pass %                    |
| `/add_student`   | Register a student                                   |
| `/add_marks`     | Enter or update marks for a student and subject      |
| `/view_results`  | Full result sheet with total, %, grade, rank, result |
| `/analysis`      | Topper, subject statistics, four charts              |

## Rules

- Grade by percentage: `A+` ≥ 90, `A` 80–89, `B+` 70–79, `B` 60–69, `C` 50–59, `D` 40–49, `F` < 40.
- A student **passes** only if every subject is ≥ 40% of its maximum marks
  (`PASS_PERCENT` in `config.py`).
- Rank is by total marks; ties share a rank.
- Marks are unique per student and subject; entering them again updates the value.
- Duplicate roll numbers / emails are blocked in the app and by `UNIQUE` constraints.

## Project structure

```
Student_Result_Analysis/
├── app.py            Flask routes
├── config.py         Database + app settings
├── database/schema.sql
├── utils/db.py       Connection helper (context-manager cursor)
├── utils/analysis.py Pandas calculations + Matplotlib charts
├── templates/        Jinja pages
└── static/           CSS and generated chart PNGs
```
