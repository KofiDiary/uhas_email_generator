# UHAS Student Email Generator

Desktop application for generating standardized UHAS student emails from Excel/CSV student records, with built-in school/programme management and bulk mapping import.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Input File Requirements](#input-file-requirements)
- [Setup Guide (PC)](#setup-guide-pc)
- [Launch Guide](#launch-guide)
- [Usage Guide](#usage-guide)
- [Bulk Upload Format](#bulk-upload-format)
- [Output Format](#output-format)
- [Troubleshooting](#troubleshooting)
- [Build Executable (Optional)](#build-executable-optional)
- [License](#license)

---

## Overview

The **UHAS Student Email Generator** helps admins process student lists and generate institution-formatted email accounts in bulk.

It provides:

- Email generation from name + student ID + admission level + programme
- Duplicate email resolution
- Export to **Excel** and **CSV**
- Error/warning reporting for problematic rows
- School/programme mapping management in-app
- Bulk import of mappings from file

---

## Key Features

- Clean desktop UI built with `customtkinter`
- Accepts `.xlsx`, `.xls`, and `.csv`
- Flexible input column detection (supports alias headers)
- Automatic suffix rules:
  - `pg` for postgraduate levels (`> 400`)
  - `sw` for sandwich students
- SQLite-backed school/programme mapping
- Pre-seeded UHAS school/programme data
- Styled Excel export (headers, borders, alternating rows, frozen top row)

---

## Tech Stack

- **Python 3.10+**
- **CustomTkinter** (GUI)
- **Pandas** (data processing)
- **OpenPyXL** (Excel export formatting)
- **SQLite** (local mapping database)

---

## Project Structure

```text
.
├── main.py
├── database.py
├── email_logic.py
├── file_handler.py
├── requirements.txt
├── .gitignore
├── data/
│   └── uhas.db (auto-created at runtime; ignored by git)
├── assets/
└── ui/
    ├── __init__.py
    ├── main_window.py
    ├── mapping_manager.py
    └── bulk_upload.py
```

---

## How It Works

1. App starts and initializes SQLite DB.
2. User uploads student file.
3. Required columns are auto-detected.
4. Each row is processed to generate email + output fields.
5. Duplicates are resolved.
6. Preview, errors, and download options are shown.

---

## Input File Requirements

Your student file must include these logical fields (aliases supported):

- Student ID (`student no`, `student number`, `index number`, `index no`, `id`)
- Name (`name`, `full name`, `fullname`, `student name`)
- Programme (`program`, `programme`, `program offered`, `programme offered`)
- Level (`level`)
- Level of Admission (`level of admission`, `admission level`, `level admitted`)

> Recommended name format: `SURNAME, OTHER NAMES`

---

## Setup Guide (PC)

### 1) Install prerequisites

- Install **Python 3.10+**
- Ensure Python is available in terminal:

```powershell
python --version
```

### 2) Open project folder

```powershell
cd path\to\uhas_email_gen
```

### 3) Create virtual environment

```powershell
python -m venv venv
```

### 4) Activate virtual environment

```powershell
venv\Scripts\activate
```

### 5) Install dependencies

```powershell
pip install -r requirements.txt
```

> If dependency install fails due to file encoding issues in `requirements.txt`, re-save it as UTF-8 and retry.

---

## Launch Guide

Run:

```powershell
python main.py
```

On first run, the app creates and seeds:

- `data/uhas.db`

---

## Usage Guide

1. **Upload file** (`.xlsx`, `.xls`, `.csv`)
2. Select student type:
   - `Regular`
   - `Sandwich` (adds `sw` suffix)
3. Click **Generate Emails**
4. Review:
   - **Preview** tab
   - **Errors / Warnings** tab
5. Download result:
   - **Excel (.xlsx)** or
   - **CSV (.csv)**
6. Maintain mappings:
   - **Manage Schools & Programmes**
   - **Bulk Upload Programmes**

---

## Bulk Upload Format

For bulk mapping import, file must have exactly these columns:

- `School Code`
- `Programme Names` (comma-separated list in a single cell)

Example:

| School Code | Programme Names |
|---|---|
| som | Bachelor of Dental Surgery, Bachelor of Medicine, Bachelor of Surgery |

Modes:

- **Merge**: add new entries, keep existing
- **Replace**: clear existing and import new

---

## Output Format

Generated file uses 16 columns including:

- Username
- First name
- Last name
- Display name
- DEPARTMENT
- Fax Number (student ID)
- Alternate email address
- City / Region defaults for valid rows

---

## Troubleshooting

- **“Missing required columns”**  
  Rename headers to match supported aliases.
- **Unsupported file type**  
  Use `.csv`, `.xlsx`, or `.xls`.
- **Startup DB error**  
  Ensure write permission to project directory.
- **Unknown department in email**  
  Programme not mapped; add it in mapping manager or bulk upload.
- **Module import errors**  
  Confirm virtual environment is active and dependencies are installed.

---

## Build Executable (Optional)

A PyInstaller spec file exists (`uhas_email_gen.spec`).

Typical command:

```powershell
pyinstaller uhas_email_gen.spec
```

---
