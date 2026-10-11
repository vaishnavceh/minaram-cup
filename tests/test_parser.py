"""
Tests for registration parser.
"""

from app.registration_parser import (
    parse_registration_text,
    clean_whatsapp_artifacts,
    split_multiple_registrations
)


def test_standard_format():
    text = """
    Registration Format
    Name: Vaishnav
    Phone No: 9746603975
    Team Name: Binladen Fc
    """
    results = parse_registration_text(text)
    assert len(results) == 1
    r = results[0]
    assert r.is_valid is True
    assert r.name == "Vaishnav"
    assert r.phone == "9746603975"
    assert r.team == "Binladen Fc"


def test_backslash_single_line():
    text = r"Name: Alex Ferguson \ Phone No: 0987654321 \ Team Name: Red Devils"
    results = parse_registration_text(text)
    assert len(results) == 1
    r = results[0]
    assert r.is_valid is True
    assert r.name == "Alex Ferguson"
    assert r.phone == "0987654321"  # Leading zero preserved!
    assert r.team == "Red Devils"


def test_whatsapp_formatted():
    text = """
    [10/11/26, 9:15 PM] Vaishnav: *Registration Format*
    *Name:* Cristiano Ronaldo
    *Mobile No:* +919876543210
    *Club Name:* Al Nassr FC
    """
    results = parse_registration_text(text)
    assert len(results) == 1
    r = results[0]
    assert r.is_valid is True
    assert r.name == "Cristiano Ronaldo"
    assert r.phone == "+919876543210"
    assert r.team == "Al Nassr FC"


def test_multiple_registrations_one_paste():
    text = """
    Registration Format
    Name: Team One Captain
    Phone No: 9111111111
    Team Name: Alpha FC

    Registration Format
    Name: Team Two Captain
    Phone No: 9222222222
    Team Name: Beta FC

    Name: Team Three Captain \\ Phone No: 9333333333 \\ Team Name: Gamma FC
    """
    results = parse_registration_text(text)
    assert len(results) == 3
    assert results[0].name == "Team One Captain"
    assert results[0].team == "Alpha FC"
    assert results[1].name == "Team Two Captain"
    assert results[1].team == "Beta FC"
    assert results[2].name == "Team Three Captain"
    assert results[2].team == "Gamma FC"


def test_missing_fields_validation():
    text = """
    Name: Incomplete Person
    Phone No: 9888888888
    """
    results = parse_registration_text(text)
    assert len(results) == 1
    assert results[0].is_valid is False
    assert any("Team Name" in err for err in results[0].errors)
