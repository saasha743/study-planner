"""
Study Planner CLI
-----------------
A simple command-line tool that stores your subjects and exam dates,
and tells you how to split your study time today.
"""

import json
import os
from datetime import datetime, date

DATA_FILE = "subjects.json"
DATE_FORMAT = "%d-%m-%Y"


# ---------- Saving and loading ----------

def load_data():
    """Read subjects from the file. Return an empty list if none exist."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_data(subjects):
    """Write the subjects list to the file."""
    with open(DATA_FILE, "w") as file:
        json.dump(subjects, file, indent=4)


# ---------- Helpers ----------

def days_left(exam_date_str):
    """Return how many days remain until the exam."""
    exam = datetime.strptime(exam_date_str, DATE_FORMAT).date()
    return (exam - date.today()).days


def ask_date():
    """Keep asking until the user enters a valid future date."""
    while True:
        text = input("Exam date (DD-MM-YYYY): ").strip()
        try:
            exam = datetime.strptime(text, DATE_FORMAT).date()
        except ValueError:
            print("Invalid date. Use DD-MM-YYYY, for example 25-12-2026.")
            continue
        if exam < date.today():
            print("That date is in the past. Enter a future date.")
            continue
        return text


def ask_number(prompt, low, high):
    """Keep asking until the user enters a whole number between low and high."""
    while True:
        text = input(prompt).strip()
        if text.isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"Please enter a number from {low} to {high}.")


# ---------- Menu actions ----------

def add_subject(subjects):
    name = input("Subject name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    exam_date = ask_date()
    difficulty = ask_number("Difficulty (1 = easy, 5 = very hard): ", 1, 5)

    subjects.append({"name": name, "exam_date": exam_date, "difficulty": difficulty})
    save_data(subjects)
    print(f"Added {name}!")


def view_subjects(subjects):
    if not subjects:
        print("No subjects yet. Add one first.")
        return

    ordered = sorted(subjects, key=lambda s: days_left(s["exam_date"]))
    print("\nYour subjects (nearest exam first):")
    print("-" * 50)
    for i, s in enumerate(ordered, start=1):
        left = days_left(s["exam_date"])
        if left < 0:
            status = "exam passed"
        elif left == 0:
            status = "exam is TODAY"
        else:
            status = f"{left} day(s) left"
        print(f"{i}. {s['name']} | {s['exam_date']} | difficulty {s['difficulty']} | {status}")


def todays_plan(subjects):
    # Only subjects whose exam has not passed
    upcoming = [s for s in subjects if days_left(s["exam_date"]) >= 0]
    if not upcoming:
        print("No upcoming exams. Add a subject first.")
        return

    while True:
        text = input("How many hours can you study today? ").strip()
        try:
            hours = float(text)
            if hours > 0:
                break
        except ValueError:
            pass
        print("Enter a number greater than 0, for example 3 or 2.5.")

    # Priority = difficulty divided by days left (closer + harder = higher)
    for s in upcoming:
        s["priority"] = s["difficulty"] / max(days_left(s["exam_date"]), 1)

    total_priority = sum(s["priority"] for s in upcoming)
    upcoming.sort(key=lambda s: s["priority"], reverse=True)

    print("\nYour study plan for today:")
    print("-" * 50)
    for s in upcoming:
        share = hours * s["priority"] / total_priority
        minutes = round(share * 60)
        print(f"{s['name']}: {minutes // 60}h {minutes % 60}m")

    # Remove the temporary priority values so they are not saved
    for s in upcoming:
        del s["priority"]


def delete_subject(subjects):
    if not subjects:
        print("Nothing to delete.")
        return

    print("\nSubjects:")
    for i, s in enumerate(subjects, start=1):
        print(f"{i}. {s['name']} ({s['exam_date']})")

    choice = ask_number("Number to delete: ", 1, len(subjects))
    removed = subjects.pop(choice - 1)
    save_data(subjects)
    print(f"Deleted {removed['name']}.")


# ---------- Main program ----------

def main():
    subjects = load_data()

    while True:
        print("\n===== STUDY PLANNER =====")
        print("1. Add subject")
        print("2. View subjects")
        print("3. Today's plan")
        print("4. Delete subject")
        print("5. Exit")

        choice = input("Choose (1-5): ").strip()

        if choice == "1":
            add_subject(subjects)
        elif choice == "2":
            view_subjects(subjects)
        elif choice == "3":
            todays_plan(subjects)
        elif choice == "4":
            delete_subject(subjects)
        elif choice == "5":
            print("Good luck with your studies!")
            break
        else:
            print("Invalid choice. Enter a number from 1 to 5.")


if __name__ == "__main__":
    main()
