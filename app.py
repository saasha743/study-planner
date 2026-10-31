import json
import os
from datetime import date, datetime, timedelta

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
        return max(1,min(5, int(subject.get("difficulty" , 1))))
    except (ValueError,TypeError):
        return 1
def safe_days_left(subject):
    try:
        return days_left(subject["exam_date"])
    except(KeyError, ValueError ,TypeError):
        return 999999

def studied_today(subject):
    logs = subject.get("studied", {})
    if not isinstance(logs, dict):
        return 0
    return int(logs.get(date.today().strftime(DATE_FORMAT), 0))

def total_studied(subject):
    logs = subject.get("studied", {})
    if not isinstance(logs, dict):
        return 0
    return sum(int(v) for v in logs.values() if isinstance(v, (int, float)))

def is_resting(subject, on_day=None):
    on_day = on_day or date.today()
    try:
        return on_day < parse_exam_date(subject["rest_until"])
    except (KeyError, ValueError, TypeError):
        return False
def study_streak(all_subjects):
    days = set()
    for s in all_subjects:
        logs = s.get("studied", {})
        if isinstance(logs, dict):
            for day_text, minutes in logs.items():
                try:
                    if int(minutes) > 0:
                        days.add(parse_exam_date(day_text))
                except (ValueError, TypeError):
                    continue
    current = date.today()
    if current not in days:
        current = current - timedelta(days=1)
    streak = 0
    while current in days:
        streak += 1
        current = current - timedelta(days=1)
    return streak
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

col1, col2, col3, col4 = st.columns(4)
col1.metric("📘 Total subjects", len(subjects))
col2.metric("🗓️ Upcoming exams", len(upcoming))
closest = min((remaining for _, remaining in upcoming), default=None)
col3.metric("⏳ Nearest exam", "Today" if closest == 0 else (f"{closest} days" if closest is not None else "—"))
col4.metric("🔥 Study streak", f"{study_streak(subjects)} day(s)")
plan_items = [(s, r) for s, r in upcoming if not is_resting(s)]

st.divider()

tab_plan, tab_subjects, tab_add, tab_progress, tab_week = st.tabs(["✨ Today's plan", "📖 My subjects", "➕ Add a subject", "📊 Progress", "📅 Week plan"])
with tab_week:
    st.subheader("Your next 7 days")
    st.write("Each day's study time is shared by urgency and difficulty, the same way as today's plan.")
    week_hours = st.number_input("Hours you can study each day", min_value=0.25, max_value=24.0, value=3.0, step=0.25, key="week_hours")
    for offset in range(7):
        plan_day = date.today() + timedelta(days=offset)
        items = []
        for s in subjects:
            if is_resting(s, plan_day):
                continue
            try:
                left = (parse_exam_date(s["exam_date"]) - plan_day).days
            except (KeyError, ValueError, TypeError):
                continue
            if left < 0:
                continue
            score = safe_difficulty(s) / max(left, 1) / (1 + total_studied(s) / 300)
            items.append((s.get("name", "Unnamed"), left, score))
        label = "Today" if offset == 0 else plan_day.strftime("%A %d %b")
        with st.container(border=True):
            st.markdown(f"*{label}*")
            if not items:
                st.caption("No exams left to plan for.")
            else:
                total_score = sum(item[2] for item in items)
                items.sort(key=lambda item: item[2], reverse=True)
                for subject_name, left, score in items:
                    minutes = round(week_hours * 60 * score / total_score)
                    hrs, mins = divmod(minutes, 60)
                    st.write(f"{subject_name} — {hrs}h {mins}m" + (" · 🎯 exam day" if left == 0 else ""))
with tab_progress:
    st.subheader("Hours studied per subject")
    rows = [
        {"Subject": s.get("name", "Unnamed"), "Hours": round(total_studied(s) / 60, 2)}
        for s in subjects
    ]
    if not rows or all(r["Hours"] == 0 for r in rows):
        st.info("No study time logged yet. Log time in the *My subjects* tab and your chart will appear here.")
    else:
        st.metric("Total hours studied", f"{sum(r['Hours'] for r in rows):.1f} h")
        st.bar_chart(rows, x="Subject", y="Hours")
with tab_plan:
    st.subheader("Build today's study plan")
    st.write("Your available study time is shared according to each subject's urgency and difficulty.")
    hours = st.number_input("How many hours can you study today?", min_value=0.25, max_value=24.0, value=3.0, step=0.25)
    if st.button("Create my study plan", type="primary", use_container_width=True):
        if not plan_items:
            st.info("No upcoming exams yet. Add a subject in the **Add a subject** tab.")
        else:
            scored = []
            for subject, remaining in plan_items:
                difficulty = safe_difficulty(subject)
                priority = difficulty / max(remaining, 1)/(1 + total_studied(subject)/300)
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
                    done = studied_today(subject)
                    st.progress(min(done / max(mins, 1), 1.0))
                    st.caption(f"Studied today: {done} of {mins} min" + (" ✅" if done >= mins else ""))

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
                    middle.markdown(":gray[Check exam date]")
                elif remaining < 0:
                    middle.markdown(":gray[Exam passed]")
                elif remaining == 0:
                    middle.markdown(":red[**🎯 Exam is today!**]")
                elif remaining <= 3:
                    middle.markdown(f":red[**{remaining} day(s) left**]")
                elif remaining <= 7:
                    middle.markdown(f":orange[**{remaining} day(s) left**]")
                else:
                    middle.markdown(f":green[{remaining} day(s) left]")
                # Match the subject in the underlying list by its data, including duplicate names.
                if right.button("Delete", key=f"delete_{idx}_{subject.get('name', 'subject')}", use_container_width=True):
                    original_index = subjects.index(subject)
                    removed = subjects.pop(original_index)
                    save_data(subjects)
                    st.session_state.subjects = subjects
                    st.success(f"Deleted {removed.get('name', 'subject')}.")
                    st.rerun()
                with st.expander("✏️ Edit this subject"):
                    with st.form(f"edit_form_{idx}"):
                        new_name = st.text_input("Subject name", value=subject.get("name", ""), key=f"edit_name_{idx}")
                        try:
                            current_date = parse_exam_date(subject["exam_date"])
                        except (KeyError, ValueError, TypeError):
                            current_date = today
                        new_date = st.date_input("Exam date", value=current_date, key=f"edit_date_{idx}")
                        new_difficulty = st.slider("Difficulty", min_value=1, max_value=5, value=safe_difficulty(subject), key=f"edit_diff_{idx}")
                        save_edit = st.form_submit_button("Save changes", type="primary")
                    if save_edit:
                        if not new_name.strip():
                            st.error("Please enter a subject name.")
                        else:
                            for s in subjects:
                                if s is subject:
                                    s["name"] = new_name.strip()
                                    s["exam_date"] = new_date.strftime(DATE_FORMAT)
                                    s["difficulty"] = new_difficulty
                            save_data(subjects)
                            st.rerun()
                    st.caption(f"Studied today: {studied_today(subject)} min · Total: {total_studied(subject) / 60:.1f} h")
                with st.expander("⏱️ Log study time"):
                    with st.form(f"log_form_{idx}"):
                        minutes_done = st.number_input("Minutes you studied", min_value=0, max_value=1440, value=30, step=5, key=f"log_min_{idx}")
                        log_submit = st.form_submit_button("Save time")
                    if log_submit and minutes_done > 0:
                        for s in subjects:
                            if s is subject:
                                logs = s.setdefault("studied", {})
                                day_key = date.today().strftime(DATE_FORMAT)
                                logs[day_key] = logs.get(day_key, 0) + int(minutes_done)
                        save_data(subjects)
                        st.rerun()
                   if is_resting(subject):
                    st.caption(f"😴 Resting until {parse_exam_date(subject['rest_until']).strftime('%d %b')}")
                with st.expander("😴 Rest this subject"):
                    with st.form(f"rest_form_{idx}"):
                        rest_days = st.number_input("Rest for how many days?", min_value=1, max_value=14, value=1, step=1, key=f"rest_days_{idx}")
                        rest_submit = st.form_submit_button("Start rest")
                    if rest_submit:
                        for s in subjects:
                            if s is subject:
                                s["rest_until"] = (date.today() + timedelta(days=int(rest_days))).strftime(DATE_FORMAT)
                        save_data(subjects)
                        st.rerun()
                    if is_resting(subject):
                        if st.button("Resume now", key=f"resume_{idx}"):
                            for s in subjects:
                                if s is subject:
                                    s.pop("rest_until", None)
                            save_data(subjects)
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
