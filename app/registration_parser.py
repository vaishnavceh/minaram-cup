"""
Robust parser for Minaram Cup registration messages.
Supports single & multiple registrations, WhatsApp formatting, backslash separation,
and custom field label variations.
"""

import re
from typing import List, Tuple
from app.models import ParsedRegistration


NAME_LABELS = [
    r"Participant\s*Name",
    r"Player\s*Name",
    r"Captain\s*Name",
    r"Captain",
    r"Name",
]

PHONE_LABELS = [
    r"Phone\s*Number",
    r"Phone\s*No\.?",
    r"Mobile\s*Number",
    r"Mobile\s*No\.?",
    r"Contact\s*No\.?",
    r"WhatsApp\s*No\.?",
    r"WhatsApp",
    r"Mobile",
    r"Phone",
    r"Contact",
    r"Tel",
]

TEAM_LABELS = [
    r"Team\s*Name",
    r"Club\s*Name",
    r"Squad\s*Name",
    r"Team",
    r"Club",
    r"Squad",
]


def clean_whatsapp_artifacts(text: str) -> str:
    """Strip WhatsApp metadata headers like [10/11/26, 9:15 PM] Vaishnav:"""
    # Remove bracketed timestamps: [10/11/2026, 21:15:30] User: ...
    text = re.sub(r"^\[\d{1,2}[/-]\d{1,2}[/-]\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\]\s*[^:]+:\s*", "", text, flags=re.MULTILINE)
    # Remove standard WhatsApp timestamp without brackets: 10/11/26, 9:15 PM - User: ...
    text = re.sub(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*-\s*[^:]+:\s*", "", text, flags=re.MULTILINE)
    # Remove markdown bold/italic asterisks around labels (e.g., *Name:* -> Name:)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    return text


def split_multiple_registrations(raw_text: str) -> List[str]:
    """
    Split pasted text containing one or many registration messages into individual chunks.
    Handles mixed delimiters: 'Registration Format', '---', multiple 'Name:' anchors, and backslashes.
    """
    cleaned = clean_whatsapp_artifacts(raw_text.strip())
    if not cleaned:
        return []

    # Normalize Windows line endings
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Find boundaries using regex: either 'Registration Format' or a new 'Name:'
    # A boundary occurs at 'Registration Format' OR at 'Name:' when a record was already started.
    lines = cleaned.split("\n")
    chunks: List[str] = []
    current_chunk_lines: List[str] = []
    current_has_name = False
    current_has_phone_or_team = False

    name_regex = re.compile(rf"(?i)(?:^|[\\|])\s*(?:{NAME_LABELS[0]}|{NAME_LABELS[1]}|{NAME_LABELS[2]}|{NAME_LABELS[3]}|{NAME_LABELS[4]})\s*[:\-\=]")
    rf_regex = re.compile(r"(?i)^\s*(?:Registration\s*Format|Registration\s*Entry|---|\={3,})\s*$")

    for line in lines:
        stripped = line.strip()
        # Check if line contains backslash-separated records or start
        if rf_regex.match(stripped):
            if current_chunk_lines:
                chunks.append("\n".join(current_chunk_lines).strip())
                current_chunk_lines = []
                current_has_name = False
                current_has_phone_or_team = False
            continue

        # Check if a new Name: appears when we already have a record being parsed
        if name_regex.search(line):
            if current_has_name and current_has_phone_or_team:
                # We have finished previous record, start a new one!
                chunks.append("\n".join(current_chunk_lines).strip())
                current_chunk_lines = []
                current_has_name = False
                current_has_phone_or_team = False
            current_has_name = True

        if any(re.search(rf"(?i)(?:^|[\\|])\s*(?:{lbl})\s*[:\-\=]", line) for lbl in (PHONE_LABELS + TEAM_LABELS)):
            current_has_phone_or_team = True

        current_chunk_lines.append(line)

    if current_chunk_lines:
        chunks.append("\n".join(current_chunk_lines).strip())

    # In case there are single lines containing multiple backslash-separated records:
    expanded_chunks: List[str] = []
    for chunk in chunks:
        # Check if a single line chunk has multiple 'Name:' inside it separated by backslashes
        # e.g., Name: Foo \ Phone: 1 \ Team: A \ Name: Bar \ Phone: 2 \ Team: B
        matches = list(name_regex.finditer(chunk))
        if len(matches) > 1:
            indices = [m.start() for m in matches]
            indices.append(len(chunk))
            for i in range(len(indices) - 1):
                sub = chunk[indices[i]:indices[i+1]].strip().strip("\\").strip()
                if sub:
                    expanded_chunks.append(sub)
        else:
            if chunk.strip():
                expanded_chunks.append(chunk)

    return expanded_chunks


def extract_field_value(chunk: str, label_regexes: List[str]) -> str:
    """
    Extract field value whether it is on its own line or separated by backslashes / slashes / commas.
    """
    # Build regex that captures from label to next delimiter or end of line/string
    labels_alt = "|".join(label_regexes)
    
    # 1. First attempt: Line-based match or backslash-based match
    # Look for Label : Value (stopping at \ or next known label or end of line)
    all_known_labels = "|".join(NAME_LABELS + PHONE_LABELS + TEAM_LABELS + [r"Registration\s*Format"])
    
    pattern = rf"(?i)(?:^|[\n\\|])\s*(?:{labels_alt})\s*[:\-\=]\s*([^\\\n|]+?)(?=(?:[\n\\|]\s*(?:{all_known_labels})\s*[:\-\=])|$)"
    match = re.search(pattern, chunk)
    if match:
        val = match.group(1).strip()
        # Clean trailing slashes or formatting
        val = val.strip("\\/").strip()
        return val

    # 2. Fallback: looser pattern matching anywhere in the line
    pattern_fallback = rf"(?i)(?:{labels_alt})\s*[:\-\=]\s*([^\n\\]+)"
    match_fb = re.search(pattern_fallback, chunk)
    if match_fb:
        val = match_fb.group(1).strip()
        val = val.strip("\\/").strip()
        return val

    return ""


def clean_phone_number(raw_phone: str) -> str:
    """Clean phone number preserving leading zeros, '+', and text formatting without stripping leading 0."""
    if not raw_phone:
        return ""
    # Remove spaces, parentheses, hyphens, dots
    cleaned = re.sub(r"[\s\(\)\-\.]", "", raw_phone.strip())
    return cleaned


def parse_single_chunk(chunk: str) -> ParsedRegistration:
    """Parse a single registration chunk into a structured ParsedRegistration."""
    normalized_chunk = chunk.replace("\\\n", "\n")
    
    name = extract_field_value(normalized_chunk, NAME_LABELS)
    phone_raw = extract_field_value(normalized_chunk, PHONE_LABELS)
    team = extract_field_value(normalized_chunk, TEAM_LABELS)
    
    phone = clean_phone_number(phone_raw)

    errors = []
    warnings = []

    if not name:
        errors.append("Missing field: Name")
    if not phone:
        errors.append("Missing field: Phone Number")
    if not team:
        errors.append("Missing field: Team Name")

    # Additional phone checks
    if phone:
        # Check if phone has invalid characters
        digits_only = re.sub(r"\D", "", phone)
        if len(digits_only) < 7:
            warnings.append(f"Phone number '{phone}' seems unusually short")
        elif len(digits_only) > 15:
            warnings.append(f"Phone number '{phone}' seems unusually long")
        if re.search(r"[a-zA-Z]", phone):
            warnings.append("Phone contains letters")

    is_valid = len(errors) == 0

    return ParsedRegistration(
        name=name,
        phone=phone,
        team=team,
        raw_text=chunk.strip(),
        is_valid=is_valid,
        errors=errors,
        warnings=warnings
    )


def parse_registration_text(raw_text: str) -> List[ParsedRegistration]:
    """
    Main entry point: parse pasted text (which may contain 1 or multiple registrations)
    and return a list of ParsedRegistration objects.
    """
    chunks = split_multiple_registrations(raw_text)
    results = []
    for chunk in chunks:
        # Ignore empty or header-only noise chunks
        stripped = chunk.strip().lower()
        if not stripped or stripped in ("registration format", "registration format:", "end"):
            continue
        parsed = parse_single_chunk(chunk)
        results.append(parsed)
    return results
