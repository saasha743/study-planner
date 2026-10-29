# Study Planner Website

This is a browser-based version of the original Study Planner CLI, built with Streamlit.

## Features
- Add subjects, exam dates, and difficulty (1–5)
- Sort subjects by nearest exam
- Generate a daily plan using `priority = difficulty / days left`
- Delete subjects
- Save subject data in `subjects.json`

## Run locally
1. Install Python 3.9 or newer.
2. Open a terminal in this folder.
3. Run:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Deploy with Streamlit Community Cloud
1. Upload `app.py` and `requirements.txt` to your GitHub repository.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**.
4. Select repository `saasha743/study-planner`, branch `main`, and main file path `app.py`.
5. Click **Deploy**.

## Note about saving data online
This starter version saves data in `subjects.json`. On hosted services, local files may not be permanent across restarts or redeployments. For long-term, multi-device storage, connect a database later.
