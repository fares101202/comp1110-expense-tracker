"""Expense input checks, CSV storage, and readable expense records."""

import csv
import os
import tempfile


CATEGORIES = ("Food", "Transport", "School", "Other")


def parse_amount(text):
    """Return positive dollar input as whole cents, or raise ValueError."""
    whole, decimal_point, fraction = text.strip().partition(".")
    if not whole.isdecimal():
        raise ValueError("Enter a positive dollar amount, such as 4.50.")
    if decimal_point and (not fraction.isdecimal() or len(fraction) > 2):
        raise ValueError("Use one or two digits after the decimal point.")

    cents = int(whole) * 100
    if decimal_point:
        cents += int(fraction.ljust(2, "0"))
    if cents == 0:
        raise ValueError("The amount must be greater than zero.")
    return cents


def validate_category(text):
    """Return a standard category name, or raise ValueError."""
    choice = text.strip().lower()
    for category in CATEGORIES:
        if choice == category.lower():
            return category
    raise ValueError("Choose Food, Transport, School, or Other.")


def format_expense(expense):
    """Return a readable line, formatting integer cents without floats."""
    cents = expense["amount_cents"]
    amount = f"${cents // 100}.{cents % 100:02d}"
    return f"[{expense['category']}] {expense['description']} - {amount}"

def load_expenses(filename="expenses.csv"):
    """Load valid CSV records; start empty for a missing file only."""
    records = []
    fields = ["description", "category", "amount_cents"]
    try:
        with open(filename, newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source, strict=True)
            if reader.fieldnames != fields:
                raise ValueError("Expense CSV has an invalid header.")
            for row in reader:
                try:
                    if None in row or None in row.values():
                        raise ValueError("Wrong number of CSV fields.")
                    description = row["description"].strip()
                    category = validate_category(row["category"])
                    cents = int(row["amount_cents"])
                    if not description or cents <= 0:
                        raise ValueError("Invalid expense values.")
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"Invalid expense at CSV line {reader.line_num}."
                    ) from error
                records.append({
                    "description": description,
                    "category": category,
                    "amount_cents": cents,
                })
    except FileNotFoundError:
        return []
    except csv.Error as error:
        raise ValueError("Expense CSV is damaged.") from error
    return records

def save_expenses(expenses, filename="expenses.csv"):
    """Validate records, then replace the CSV only after writing succeeds."""
    records = []
    for expense in expenses:
        description = expense["description"].strip()
        category = validate_category(expense["category"])
        cents = expense["amount_cents"]
        if not description or type(cents) is not int or cents <= 0:
            raise ValueError("Cannot save an invalid expense.")
        records.append({
            "description": description,
            "category": category,
            "amount_cents": cents,
        })

    directory = os.path.dirname(os.path.abspath(filename))
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8",
            dir=directory, prefix=".expenses-", suffix=".tmp", delete=False,
        ) as target:
            temporary_name = target.name
            writer = csv.DictWriter(
                target, fieldnames=["description", "category", "amount_cents"]
            )
            writer.writeheader()
            writer.writerows(records)
        os.replace(temporary_name, filename)
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.remove(temporary_name)


def main():
    """Let the user try the expense amount and category checks."""
    print("Expense tracker input check")
    try:
        cents = parse_amount(input("Amount in dollars: "))
        category = validate_category(input("Category: "))
    except ValueError as error:
        print(f"Invalid expense: {error}")
        return

    dollars = cents // 100
    remainder = cents % 100
    print(f"Valid expense input: {category} - ${dollars}.{remainder:02d}")


def total_spending(expenses):
    """Return total spending in whole cents, or zero for no expenses."""
    total = 0
    for expense in expenses:
        total += expense["amount_cents"]
    return total


if __name__ == "__main__":
    main()
