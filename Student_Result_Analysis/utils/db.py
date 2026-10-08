"""MySQL connection helpers."""
from contextlib import contextmanager

import mysql.connector

from config import Config


def get_connection():
    """Open a new MySQL connection using the settings in config.py."""
    return mysql.connector.connect(**Config.DB_CONFIG)


@contextmanager
def get_cursor(dictionary=True, commit=False):
    """Yield a cursor; commit on success if requested, roll back on error.

        with get_cursor(commit=True) as cur:
            cur.execute("INSERT ...", params)
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def fetch_all(sql, params=None):
    """Run a SELECT and return all rows as a list of dicts."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def fetch_one(sql, params=None):
    """Run a SELECT and return the first row as a dict (or None)."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql, params=None):
    """Run INSERT / UPDATE / DELETE and commit. Returns the last row id."""
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid
