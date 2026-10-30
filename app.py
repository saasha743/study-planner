import json
import os
from datetime import date, datetime

import streamlit as st

DATA_FILE = "subjects.json"
DATE_FORMAT = "%d-%m-%Y"

st.set_page_config(
    page_title="Study Planner",
    page_icon="📚",
    layout="wide",
)

def load_data():
    """Load saved subjects. Return an empty list if no usable data exists."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_data(subjects):
    """Save subjects to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(subjects, file, indent=4)

def parse_exam_date(value):
    return datetime.strptime(value, DATE_FORMAT).date()

def days_left(exam_date_str):
    return (parse_exam_date(exam_date_str) - date.today()).days

def format_date(value):
    return parse_exam_date(value).strftime("%d %b %Y")
def safe_difficulty(subject):
    try:
        return max(1,min(5, int(subject.get("difficulty" , 1)))
    except (ValueError,TypeError):
        return 1
def safe_days_left(subject):
    try:
        return days_left(subject["exam_date"])
    except(KeyError, ValueError ,TypeError):
        return 999999
if "subjects" not in st.session_state:
    st.session_state.subjects =load_data()
                    

if "subjects" not in st.session_state:
    st.session_state.subjects = load_data()

subjects = st.session_state.subjects

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1150px;}
    .hero {
      padding: 1.6rem 1.8rem; border-radius: 22px;
      background: linear-gradient(120deg, #eee9ff 0%, #e7f4ff 100%);
      border: 1px solid #ded8f6; margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0; color: #29234b; font-size: 2.35rem;}
    .hero p {margin: .45rem 0 0; color: #57536d; font-size: 1.05rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>📚 Your Study Planner</h1>
      <p>A calmer way to plan your study time, one exam at a time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

today = date.today()
upcoming = []
for subject in subjects:
    try:
        remaining = days_left(subject["exam_date"])
        if remaining >= 0:
            upcoming.append((subject, remaining))
    except (KeyError, ValueError, TypeError):
        continue

col1, col2, col3 = st.columns(3)
col1.metric("📘 Total subjects", len(subjects))
col2.metric("🗓️ Upcoming exams", len(upcoming))
closest = min((remaining for _, remaining in upcoming), default=None)
col3.metric("⏳ Nearest exam", "Today" if closest == 0 else (f"{closest} days" if closest is not None else "—"))

st.divider()

tab_plan, tab_subjects, tab_add = st.tabs(["✨ Today's plan", "📖 My subjects", "➕ Add a subject"])

with tab_plan:
    st.subheader("Build today's study plan")
    st.write("Your available study time is shared according to each subject's urgency and difficulty.")
    hours = st.number_input("How many hours can you study today?", min_value=0.25, max_value=24.0, value=3.0, step=0.25)
    if st.button("Create my study plan", type="primary", use_container_width=True):
        if not upcoming:
            st.info("No upcoming exams yet. Add a subject in the **Add a subject** tab.")
        else:
            scored = []
            for subject, remaining in upcoming:
                difficulty = safe_difficulty(subject)
                priority = difficulty / max(remaining, 1)
                scored.append((subject, remaining, priority))
            total_priority = sum(item[2] for item in scored)
            scored.sort(key=lambda item: item[2], reverse=True)

            st.success("Here is how you can use your study time today.")
            minutes_total = round(hours * 60)
            allocated = []
            for subject, remaining, priority in scored:
                mins = round(minutes_total * priority / total_priority)
                allocated.append((subject, remaining, priority, mins))
            # Adjust rounding so the displayed minutes add up to the chosen total.
            if allocated:
                difference = minutes_total - sum(item[3] for item in allocated)
                first = allocated[0]
                allocated[0] = (first[0], first[1], first[2], first[3] + difference)

            for subject, remaining, priority, mins in allocated:
                hours_part, mins_part = divmod(max(mins, 0), 60)
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{subject['name']}**")
                    c1.caption("Exam today" if remaining == 0 else f"{remaining} day(s) until exam")
                    c2.markdown(f"### {hours_part}h {mins_part}m")
                    st.progress(min(max(priority / max(item[2] for item in scored), 0.0), 1.0))

with tab_subjects:
    st.subheader("Your subjects")
    if not subjects:
        st.info("Your subject list is empty. Add your first subject to get started.")
    else:
        sorted_subjects = sorted(
            subjects,
            key=safe_days_left
        )
        for idx, subject in enumerate(sorted_subjects):
            try:
                remaining = days_left(subject["exam_date"])
                date_label = format_date(subject["exam_date"])
            except (KeyError, ValueError):
                remaining, date_label = None, subject.get("exam_date", "Unknown date")
            with st.container(border=True):
                left, middle, right = st.columns([3, 2, 1])
                left.markdown(f"**{subject.get('name', 'Unnamed subject')}**")
                left.caption(f"Exam date: {date_label}")
                difficulty = int(subject.get("difficulty", 1))
                middle.write(f"Difficulty: **{difficulty}/5**")
                if remaining is None:
                    middle.caption("Check exam date")
                elif remaining < 0:
                    middle.caption("Exam passed")
                elif remaining == 0:
                    middle.caption("🎯 Exam is today!")
                else:
                    middle.caption(f"{remaining} day(s) left")
                # Match the subject in the underlying list by its data, including duplicate names.
                if right.button("Delete", key=f"delete_{idx}_{subject.get('name', 'subject')}", use_container_width=True):
                    original_index = subjects.index(subject)
                    removed = subjects.pop(original_index)
                    save_data(subjects)
                    st.session_state.subjects = subjects
                    st.success(f"Deleted {removed.get('name', 'subject')}.")
                    st.rerun()

with tab_add:
    st.subheader("Add a new subject")
    with st.form("add_subject_form", clear_on_submit=True):
        name = st.text_input("Subject name", placeholder="e.g. Mathematics")
        exam_day = st.date_input("Exam date", min_value=today, value=today)
        difficulty = st.slider("How difficult is this subject?", min_value=1, max_value=5, value=3)
        st.caption("1 = Easy · 5 = Very hard")
        submitted = st.form_submit_button("Add subject", type="primary", use_container_width=True)

    if submitted:
        cleaned_name = name.strip()
        if not cleaned_name:
            st.error("Please enter a subject name.")
        else:
            subjects.append({
                "name": cleaned_name,
                "exam_date": exam_day.strftime(DATE_FORMAT),
                "difficulty": difficulty,
            })
            save_data(subjects)
            st.session_state.subjects = subjects
            st.success(f"Added {cleaned_name}!")
            st.rerun()

st.divider()
st.caption("Study Planner · Plan smart, study calmly. Data is stored in a local JSON file.")
