# Study Planner CLI

A simple command-line tool that helps students decide what to study today.
Enter your subjects, exam dates and difficulty, and it splits your study hours based on which exams are closest and hardest.

## Features
- Add subjects with exam date and difficulty (1 to 5)
- View subjects sorted by nearest exam
- Get a daily study plan based on the hours you have
- Delete subjects
- Data is saved automatically in subjects.json

## How it works
Each subject gets a priority score:


priority = difficulty / days left


Your study hours for the day are shared in proportion to these scores, so harder subjects with closer exams get more time.

## Requirements
- Python 3.6 or newer (no extra libraries needed)

## How to run

python planner.py


## Sample output

===== STUDY PLANNER =====
1. Add subject
2. View subjects
3. Today's plan
4. Delete subject
5. Exit
Choose (1-5): 3
How many hours can you study today? 3

Your study plan for today:
--------------------------------------------------
Maths: 1h 41m
Physics: 0h 53m
English: 0h 26m


## Future ideas
- Reminders for upcoming exams
- Study streak tracker
- Export plan to a text file

## Author
saasha
