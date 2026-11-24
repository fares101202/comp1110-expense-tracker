"""Check Fares's expense input validation."""

import pytest

import project

from project import parse_amount, validate_category


def test_parse_amount():
    """Check exact cents, whitespace, small amounts, and invalid input."""
    valid_amounts = {
        "4": 400,
        "4.5": 450,
        "4.50": 450,
        " 4.50 ": 450,
        "0.01": 1,
        "0.10": 10,
        "0.29": 29,
        "0004.50": 450,
        "90071992547409.93": 9007199254740993,
    }
    for text, expected in valid_amounts.items():
        assert parse_amount(text) == expected

    invalid_amounts = [
        "", " ", "0", "0.00", "-1", "+1", "abc", "4.", ".50",
        "1.001", "4.500", "1.2.3", "NaN", "Infinity", "1e2", "$4",
        "1,000", "4 .50", "4. 50",
    ]
    for text in invalid_amounts:
        with pytest.raises(ValueError):
            parse_amount(text)


def test_validate_category():
    """Check every category, normalized input, and rejected choices."""
    for category in ("Food", "Transport", "School", "Other"):
        assert validate_category(category) == category
        assert validate_category(category.upper()) == category
        assert validate_category(" " + category.lower() + " ") == category

    for text in ("", " ", "Shopping", "Foods", "1", "Food Transport"):
        with pytest.raises(ValueError):
            validate_category(text)


def test_format_expense():
    """Display cents exactly, including tiny and very large amounts."""
    expense = {"description": "Snack", "category": "Food", "amount_cents": 1}
    assert project.format_expense(expense) == "[Food] Snack - $0.01"
    expense["amount_cents"] = 450
    assert project.format_expense(expense) == "[Food] Snack - $4.50"
    expense["amount_cents"] = 9007199254740993
    assert project.format_expense(expense).endswith("$90071992547409.93")


def test_load_expenses(tmp_path):
    """Distinguish a missing file, valid records, and damaged records."""
    path = tmp_path / "expenses.csv"
    assert project.load_expenses(path) == []
    path.write_text(
        "description,category,amount_cents\nBus,Transport,300\n",
        encoding="utf-8",
    )
    assert project.load_expenses(path) == [{
        "description": "Bus", "category": "Transport", "amount_cents": 300,
    }]
    for bad_row in [
        "Bus,Transport,abc", "Bus,Travel,300", "Bus,Food,0",
        ",Food,100", "Bus,Food", "Bus,Food,100,extra",
    ]:
        path.write_text(
            "description,category,amount_cents\n" + bad_row + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="CSV line"):
            project.load_expenses(path)
    path.write_text("wrong,header\n", encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        project.load_expenses(path)


def test_save_expenses(tmp_path, monkeypatch):
    """Round-trip CSV punctuation and protect the old file on failure."""
    path = tmp_path / "expenses.csv"
    records = [{
        "description": 'Lunch, "large"',
        "category": "Food", "amount_cents": 450,
    }]
    project.save_expenses(records, path)
    assert project.load_expenses(path) == records
    previous = path.read_bytes()
    with pytest.raises(ValueError):
        project.save_expenses([dict(records[0], amount_cents=-1)], path)
    assert path.read_bytes() == previous

    def fail_replace(source, destination):
        """Simulate a disk failure at the final save step."""
        raise OSError("Cannot replace file")

    monkeypatch.setattr(project.os, "replace", fail_replace)
    with pytest.raises(OSError, match="Cannot replace"):
        project.save_expenses([], path)
    assert path.read_bytes() == previous
    assert list(tmp_path.glob(".expenses-*.tmp")) == []


def test_total_spending():
    """Add exact cents and handle an empty list without special cases."""
    records = [{"amount_cents": cents} for cents in (450, 200, 300)]
    assert project.total_spending(records) == 950
    assert project.total_spending([]) == 0
    assert project.total_spending([{"amount_cents": 1}]) == 1
