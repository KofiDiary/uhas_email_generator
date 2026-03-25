import re
from database import get_school_code_for_programme


# ─── NAME PARSING ───

def parse_name(full_name):
    # Accepts a name in the format: SURNAME, OTHER NAMES
    # Returns a dict with keys: surname, other_names, first_name
    # other_names is everything after the comma as a list of name parts
    # first_name is the first word in other_names (used for output First name column)

    if not full_name or not str(full_name).strip():
        return {"surname": "", "other_names": [], "first_name": ""}

    full_name = str(full_name).strip()

    if "," in full_name:
        # Split on first comma only to handle edge cases
        comma_index = full_name.index(",")
        surname_part = full_name[:comma_index].strip()
        others_part = full_name[comma_index + 1:].strip()
    else:
        # No comma present - treat entire string as surname, no other names
        surname_part = full_name.strip()
        others_part = ""

    # Normalize surname - preserve hyphens, strip extra spaces
    surname = _normalize_name_part(surname_part)

    # Split other names into individual words
    other_name_parts = [
        _normalize_name_part(p) for p in others_part.split() if p.strip()
    ]

    first_name = other_name_parts[0] if other_name_parts else ""

    return {
        "surname": surname,
        "other_names": other_name_parts,
        "first_name": first_name,
    }


def _normalize_name_part(name_part):
    # Title-cases a name part while preserving hyphens
    # Example: adzo-da -> Adzo-Da, VICTORIA -> Victoria
    if not name_part:
        return ""
    if "-" in name_part:
        return "-".join(segment.capitalize() for segment in name_part.split("-"))
    return name_part.strip().capitalize()


# ─── EMAIL USERNAME BUILDING ───

def build_username(surname, other_names):
    # Builds the username prefix from initials of other names + full surname
    # surname: string (may contain hyphens)
    # other_names: list of name part strings
    # Returns lowercase username string

    if not surname:
        return ""

    # Extract first letter of each name in other names
    initials = ""
    for name in other_names:
        clean = name.strip()
        if clean:
            initials += clean[0].lower()

    # Lowercase full surname, preserve hyphens, remove any remaining spaces
    surname_clean = surname.lower().replace(" ", "")

    return f"{initials}{surname_clean}"


# ─── YEAR EXTRACTION ───

def extract_year_from_id(student_id):
    # Extracts the 4-digit admission year from a student ID
    # Expected format: UHAS{YEAR}{RANDOM_DIGITS} e.g. UHAS202500043
    # Returns the last 2 digits of the year as a string e.g. "25"
    # Returns empty string if extraction fails

    if not student_id or not str(student_id).strip():
        return ""

    student_id = str(student_id).strip().upper()

    # Remove the UHAS prefix and read the next 4 characters as the year
    if student_id.startswith("UHAS"):
        year_part = student_id[4:8]
        if year_part.isdigit() and len(year_part) == 4:
            return year_part[-2:]

    # Fallback: try to find any 4-digit year pattern in the ID
    match = re.search(r"(20\d{2})", student_id)
    if match:
        return match.group(1)[-2:]

    return ""


# ─── SUFFIX BUILDING ───

def build_suffix(year_2digit, level_of_admission, student_type):
    # Builds the suffix appended after the username
    # year_2digit: 2-character string e.g. "25"
    # level_of_admission: integer e.g. 100, 200, 500
    # student_type: string "Regular" or "Sandwich"
    # Returns suffix string e.g. "25", "25pg", "25sw", "25pgsw"

    suffix = str(year_2digit)

    # Append pg if level of admission is greater than 400
    if int(level_of_admission) > 400:
        suffix += "pg"

    # Append sw if student type is sandwich
    if str(student_type).strip().lower() == "sandwich":
        suffix += "sw"

    return suffix


# ─── SCHOOL RESOLUTION ───

def resolve_school(programme_name):
    # Looks up the school code for a given programme from the database
    # Returns the school code string or "unknown" if not found
    if not programme_name or not str(programme_name).strip():
        return "unknown"

    code = get_school_code_for_programme(str(programme_name).strip())
    return code if code else "unknown"


# ─── FULL EMAIL GENERATION ───

def generate_email(full_name, student_id, programme, level_of_admission, student_type):
    # Orchestrates the full email generation for a single student row
    # Returns a dict with all derived fields needed for the output file

    result = {
        "email": "",
        "username": "",
        "first_name": "",
        "last_name": "",
        "display_name": "",
        "department": "",
        "error": None,
    }

    # Parse name
    parsed = parse_name(full_name)
    surname = parsed["surname"]
    other_names = parsed["other_names"]
    first_name = parsed["first_name"]

    if not surname:
        result["error"] = "Could not parse surname from name field."
        return result

    # Build username prefix
    username_base = build_username(surname, other_names)

    # Extract year from student ID
    year_2digit = extract_year_from_id(student_id)
    if not year_2digit:
        result["error"] = f"Could not extract year from student ID '{student_id}'."
        return result

    # Validate level of admission
    try:
        level_int = int(level_of_admission)
    except (ValueError, TypeError):
        result["error"] = f"Invalid level of admission value: '{level_of_admission}'."
        return result

    # Build suffix
    suffix = build_suffix(year_2digit, level_int, student_type)

    # Resolve school from programme
    department = resolve_school(programme)

    # Assemble full email
    email = f"{username_base}{suffix}@{department}.uhas.edu.gh"

    # Build display name: Surname followed by all other names in original order
    display_name = surname
    if other_names:
        display_name += " " + " ".join(other_names)

    # Last name in output is surname, first name is first of the other names
    result["email"] = email
    result["username"] = f"{username_base}{suffix}"
    result["first_name"] = first_name
    result["last_name"] = surname
    result["display_name"] = display_name
    result["department"] = department.upper()

    return result


# ─── DUPLICATE HANDLING ───

def resolve_duplicates(email_list):
    # Accepts a list of generated email strings
    # Returns a new list where duplicate emails have a numeric suffix appended
    # Example: if vaadzoda25@som.uhas.edu.gh appears twice,
    # the second becomes vaadzoda25_2@som.uhas.edu.gh

    seen = {}
    resolved = []

    for email in email_list:
        if not email or "@" not in email:
            resolved.append(email)
            continue

        local, domain = email.split("@", 1)

        if local not in seen:
            seen[local] = 1
            resolved.append(email)
        else:
            seen[local] += 1
            new_local = f"{local}_{seen[local]}"
            resolved.append(f"{new_local}@{domain}")

    return resolved