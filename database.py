import sqlite3
import os
import pandas as pd

# Default path for the SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "uhas.db")


def get_connection():
    # Returns a connection to the SQLite database
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    # Creates tables if they do not already exist and seeds default data
    conn = get_connection()
    cursor = conn.cursor()

    # Create schools table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL COLLATE NOCASE,
            name TEXT NOT NULL
        )
    """)

    # Create programmes table with foreign key to schools
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programmes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            programme_name TEXT NOT NULL COLLATE NOCASE,
            FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
            UNIQUE(school_id, programme_name)
        )
    """)

    conn.commit()

    # Seed default schools and programmes if tables are empty
    cursor.execute("SELECT COUNT(*) FROM schools")
    if cursor.fetchone()[0] == 0:
        _seed_defaults(cursor)
        conn.commit()

    conn.close()


def _seed_defaults(cursor):
    # Inserts the default UHAS schools and their programmes
    default_data = {
        ("sonam", "School of Nursing and Midwifery"): [
            "BACHELOR OF MIDWIFERY",
            "BACHELOR OF NURSING",
            "BACHELOR OF PUBLIC HEALTH NURSING",
            "BACHELOR OF HEALTH SERVICES ADMINISTRATION",
            "MASTER OF PHILOSOPHY (NURSING STUDIES)",
            "MASTER PHILOSOPHY (MIDWIFERY)",
        ],
        ("sop", "School of Pharmacy"): [
            "DOCTOR OF PHARMACY",
            "DOCTOR OF PHILOSOPHY (PHARMACOGNOSY)",
            "MASTER OF PHILOSOPHY (PHARMACEUTICAL CHEMISTRY)",
            "MASTER OF PHILOSOPHY (PHARMACOLOGY)",
            "MASTER PHILOSOPHY (PHARMACOGNOSY)",
            "DOCTOR OF PHILOSOPHY (PHARMACOLOGY)",
        ],
        ("sbbs", "School of Basic and Biomedical Sciences"): [
            "BSC. BIOCHEMISTRY AND MOLECULAR BIOLOGY",
            "DOCTOR OF PHILOSOPHY (BIOMEDICAL SCIENCES)",
            "MASTER OF PHILOSOPHY (BIOMEDICAL SCIENCES)",
        ],
        ("som", "School of Medicine"): [
            "BACHELOR OF DENTAL SURGERY",
            "BACHELOR OF MEDICINE, BACHELOR OF SURGERY",
            "COMBINED BACHELOR AND MASTER OF SCIENCE IN PSYCHOLOGY (CLINICAL TOP-UP)",
            "COMBINED BACHELOR AND MASTER OF SCIENCE IN PSYCHOLOGY (CLINICAL)",
            "COMBINED BACHELOR AND MASTER OF SCIENCE IN PSYCHOLOGY (COUNSELLING)",
            "COMBINED BACHELOR AND MASTER OF SCIENCE IN PSYCHOLOGY (NEUROPSYCHOLOGY TOP-UP)",
            "COMBINED BACHELOR AND MASTER OF SCIENCE IN PSYCHOLOGY (NEUROPSYCHOLOGY)",
        ],
        ("sph", "School of Public Health"): [
            "BACHELOR OF PUBLIC HEALTH (HEALTH PROMOTION)",
            "BACHELOR OF PUBLIC HEALTH (HEALTH INFORMATION)",
            "BACHELOR OF PUBLIC HEALTH (DISEASE CONTROL)",
            "BACHELOR OF PUBLIC HEALTH (NUTRITION)",
            "DOCTOR OF PHILOSOPHY (PUBLIC HEALTH)",
            "MASTER OF PHILOSOPHY (APPLIED EPIDEMIOLOGY)",
            "MASTER OF PUBLIC HEALTH (EPIDEMIOLOGY AND DISEASE CONTROL)",
            "MASTER OF PUBLIC HEALTH (EPIDEMIOLOGY AND DISEASE CONTROL) WEEKEND OPTION",
            "MASTER OF PUBLIC HEALTH (FAMILY AND REPRODUCTIVE HEALTH)",
            "MASTER OF PUBLIC HEALTH (FAMILY AND REPRODUCTIVE HEALTH) WEEKEND OPTION",
            "MASTER OF PUBLIC HEALTH (GENERAL)",
            "MASTER OF PUBLIC HEALTH (GENERAL) WEEKEND OPTION",
            "MASTER OF PUBLIC HEALTH (HEALTH PROMOTION) WEEKEND OPTION",
        ],
        ("sahs", "School of Allied Health Sciences"): [
            "BACHELOR OF DIAGNOSTIC IMAGING (RADIOGRAPHY)",
            "BACHELOR OF DIETETICS",
            "BACHELOR OF SPEECH, LANGUAGE AND HEARING SCIENCES",
            "BACHELOR OF ORTHOTICS AND PROSTHETICS",
            "BACHELOR OF PHYSIOTHERAPY",
            "DOCTOR OF MEDICAL LABORATORY (SANDWICH)",
            "DOCTOR OF MEDICAL LABORATORY SCIENCES",
            "DOCTOR OF MEDICAL LABORATORY SCIENCES (TOP UP)",
            "MASTER OF PHILOSOPHY IN MEDICAL LABORATORY SCIENCES (CHEMICAL PATHOLOGY)",
            "MASTER OF PHILOSOPHY IN MEDICAL LABORATORY SCIENCES (HAEMATOLOGY)",
            "MASTER OF PHILOSOPHY IN MEDICAL LABORATORY SCIENCES (HISTOPATHOLOGY/CYTOPATHOLOGY)",
            "MASTER OF PHILOSOPHY IN MEDICAL LABORATORY SCIENCES (IMMUNOLOGY/VACCINOLOGY)",
            "MASTER OF SCIENCE (BIOMEDICAL SCIENCES)",
            "PHD IN MEDICAL LABORATORY SCIENCES (CLINICAL MICROBIOLOGY)",
            "PHD IN MEDICAL LABORATORY SCIENCES (HISTOPATHOLOGY/CYTOPATHOLOGY)",
        ],
        ("ssem", "School of Sports and Exercise Medicine"): [
            "BACHELOR OF SPORTS AND EXERCISE MEDICAL SCIENCES",
            "SPORTS NUTRITION",
        ],
    }

    for (code, name), programmes in default_data.items():
        cursor.execute(
            "INSERT OR IGNORE INTO schools (code, name) VALUES (?, ?)",
            (code.lower(), name)
        )
        cursor.execute("SELECT id FROM schools WHERE code = ?", (code.lower(),))
        school_id = cursor.fetchone()[0]
        for prog in programmes:
            cursor.execute(
                "INSERT OR IGNORE INTO programmes (school_id, programme_name) VALUES (?, ?)",
                (school_id, prog.upper())
            )


# ─── SCHOOL OPERATIONS ───

def get_all_schools():
    # Returns a list of all schools as dicts with id, code, name
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, name FROM schools ORDER BY code")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "code": r[1], "name": r[2]} for r in rows]


def add_school(code, name):
    # Adds a new school. Returns (True, None) on success or (False, error_message)
    if not code or not name:
        return False, "School code and name are required."
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO schools (code, name) VALUES (?, ?)",
            (code.strip().lower(), name.strip())
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"A school with code '{code}' already exists."
    finally:
        conn.close()


def rename_school(school_id, new_code, new_name):
    # Renames a school's code and/or display name
    if not new_code or not new_name:
        return False, "School code and name are required."
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE schools SET code = ?, name = ? WHERE id = ?",
            (new_code.strip().lower(), new_name.strip(), school_id)
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"A school with code '{new_code}' already exists."
    finally:
        conn.close()


def delete_school(school_id):
    # Deletes a school and all its programmes (cascade)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM schools WHERE id = ?", (school_id,))
    conn.commit()
    conn.close()
    return True, None


# ─── PROGRAMME OPERATIONS ───

def get_programmes_for_school(school_id):
    # Returns a list of programme dicts for a given school id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, programme_name FROM programmes WHERE school_id = ? ORDER BY programme_name",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "programme_name": r[1]} for r in rows]


def add_programme(school_id, programme_name):
    # Adds a programme to a school. Returns (True, None) or (False, error_message)
    if not programme_name:
        return False, "Programme name cannot be empty."
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO programmes (school_id, programme_name) VALUES (?, ?)",
            (school_id, programme_name.strip().upper())
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"Programme '{programme_name}' already exists in this school."
    finally:
        conn.close()


def remove_programme(programme_id):
    # Removes a programme by its id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM programmes WHERE id = ?", (programme_id,))
    conn.commit()
    conn.close()
    return True, None


def get_school_code_for_programme(programme_name):
    # Looks up the school code for a given programme name (case-insensitive)
    # Returns the school code string or None if not found
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.code
        FROM programmes p
        JOIN schools s ON p.school_id = s.id
        WHERE UPPER(p.programme_name) = UPPER(?)
    """, (programme_name.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ─── BULK UPLOAD ───

def bulk_upload_from_dataframe(df, merge=True):
    # Processes a DataFrame with columns School Code and Programme Names
    # merge=True keeps existing data and adds new entries
    # merge=False clears all schools before inserting
    # Returns (success_count, error_list)

    required_cols = {"school code", "programme names"}
    actual_cols = {c.strip().lower() for c in df.columns}
    missing = required_cols - actual_cols
    if missing:
        return 0, [f"Missing required columns: {', '.join(missing)}"]

    # Normalize column names for access
    col_map = {c.strip().lower(): c for c in df.columns}
    code_col = col_map["school code"]
    prog_col = col_map["programme names"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    if not merge:
        cursor.execute("DELETE FROM programmes")
        cursor.execute("DELETE FROM schools")
        conn.commit()

    success_count = 0
    errors = []

    for idx, row in df.iterrows():
        raw_code = str(row[code_col]).strip().lower()
        raw_progs = str(row[prog_col]).strip()

        if not raw_code or raw_code == "nan":
            errors.append(f"Row {idx + 2}: Missing school code.")
            continue

        # Derive a display name from the code if not available
        school_name = raw_code.upper()

        # Insert school if not exists
        cursor.execute(
            "INSERT OR IGNORE INTO schools (code, name) VALUES (?, ?)",
            (raw_code, school_name)
        )
        cursor.execute("SELECT id FROM schools WHERE code = ?", (raw_code,))
        school_row = cursor.fetchone()
        if not school_row:
            errors.append(f"Row {idx + 2}: Could not resolve school '{raw_code}'.")
            continue
        school_id = school_row[0]

        # Split programmes by comma
        programmes = [p.strip().upper() for p in raw_progs.split(",") if p.strip()]
        for prog in programmes:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO programmes (school_id, programme_name) VALUES (?, ?)",
                    (school_id, prog)
                )
                success_count += 1
            except sqlite3.IntegrityError as e:
                errors.append(f"Row {idx + 2}, Programme '{prog}': {str(e)}")

    conn.commit()
    conn.close()
    return success_count, errors