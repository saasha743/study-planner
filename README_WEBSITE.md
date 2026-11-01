# Study Planner Website

*Live app:* https://study-planner-xdviu4euzmgbqjpz2a2tlp.streamlit.app/

This is a browser-based version of the original Study Planner CLI, built with Streamlit. It tells you what to study today based on your exam dates and subject difficulty, and it tracks how well you are following the plan.

## Features

*Planning*
- Quick add: tick common subjects, set an exam date and difficulty for each, and add them all at once (or add a custom subject)
- Edit or delete subjects, sorted by nearest exam, with colour-coded countdowns (red: 3 days or less, orange: 7 days or less, green: more than 7 days)
- Today's plan: enter your study hours and get a time split per subject
- Week plan: a plan for each of the next 7 days
- Rest option: pause a subject for a few days and the plans skip it

*Tracking*
- Log the minutes you actually studied for each subject
- Today's plan shows studied time against planned time with a progress bar
- Pomodoro timer: focus and break countdown, and every finished focus session is logged to the subject you pick
- Study streak: how many days in a row you have studied
- Progress tab: chart of hours studied per subject
- Performance tab: set a daily goal (saved between visits) and get a weekly score out of 100, a short verdict, and warnings for subjects with an exam within 7 days that you are neglecting
- Checklist tab: tick off each subject you finished today, and keep a topic checklist for every subject
- Notes tab: write and save notes for each subject, including general subjects you have not added yet

*Design*
- A warm cream and terracotta theme with card-style sections

## How the plan is calculated

Each subject gets a priority score:

priority = difficulty / days left / (1 + minutes studied / 300)

Your available hours are shared between subjects in proportion to their priority. Exams that are closer and harder subjects get more time, and subjects you have already studied a lot get slightly less.

## Data storage

Subjects, notes and settings are saved in subjects.json and settings.json. Because hosted apps lose local files when they sleep or restart, the app can also copy the data to a private GitHub repository (study-planner-data) so it is not lost. This uses a GitHub access token stored in Streamlit's Secrets (GITHUB_TOKEN and GITHUB_REPO), never in the code. Without these secrets the app still works and falls back to the local files.

## Run locally

1. Install Python 3.9 or newer.
2. Open a terminal in this folder.
3. Run pip install -r requirements.txt
4. Run streamlit run app.py

## Deploy with Streamlit Community Cloud

1. Upload app.py and requirements.txt to your GitHub repository.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose Create app.
4. Select repository saasha743/study-planner, branch main, and main file path app.py.
5. Click Deploy
