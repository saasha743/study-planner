import json
import base64
import requests
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

def cloud_settings():
    try:
        return st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"]
    except Exception:
        return None, None

def cloud_url(repo):
    return f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"

def cloud_headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

def load_local():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def load_data():
    """Load subjects from the private GitHub data repo, or from the local file."""
    token, repo = cloud_settings()
    st.session_state["cloud_ok"] = False
    if token:
        try:
            reply = requests.get(cloud_url(repo), headers=cloud_headers(token), timeout=15)
            if reply.status_code == 200:
                text = base64.b64decode(reply.json()["content"]).decode("utf-8")
                data = json.loads(text)
                st.session_state["cloud_ok"] = True
                return data if isinstance(data, list) else []
            if reply.status_code == 404:
                st.session_state["cloud_ok"] = True
                return []
        except Exception:
            pass
    return load_local()

def save_data(subjects):
    """Save subjects locally and, when connected, to the private GitHub data repo."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(subjects, file, indent=4)
    token, repo = cloud_settings()
    if token and st.session_state.get("cloud_ok"):
        try:
            url = cloud_url(repo)
            headers = cloud_headers(token)
            existing = requests.get(url, headers=headers, timeout=15)
            body = {
                "message": "Update study planner data",
                "content": base64.b64encode(json.dumps(subjects, indent=2).encode("utf-8")).decode("ascii"),
            }
            if existing.status_code == 200:
                body["sha"] = existing.json()["sha"]
            result = requests.put(url, headers=headers, json=body, timeout=15)
            st.session_state["cloud_error"] = result.status_code not in (200, 201)
        except Exception:
            st.session_state["cloud_error"] = True
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
if cloud_settings()[0] and not st.session_state.get("cloud_ok", False):
    st.warning("Permanent storage could not be reached, so your changes may be lost when the app sleeps. Refresh the page to try again.")
if st.session_state.get("cloud_error"):
    st.warning("The last save to permanent storage failed. Your data is safe on screen but may not be stored yet.")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1050px;}
    .stApp {background: linear-gradient(180deg, #fbf6ef 0%, #f6ebdd 100%);}
    h1, h2, h3 {font-family: Georgia, "Times New Roman", serif !important; color: #3b2f2a;}
    .hero {
      padding: 1.6rem 1.8rem; border-radius: 20px;
      background: linear-gradient(120deg, #f6e7d4 0%, #efd9be 100%);
      border: 1px solid #e3cdb1; margin-bottom: 1.2rem;
      box-shadow: 0 4px 14px rgba(120, 80, 40, .10);
    }
    .hero h1 {margin: 0; color: #4a3428; font-size: 2.2rem;}
    .hero p {margin: .45rem 0 0; color: #7a5f4d; font-size: 1.05rem;}
    [data-testid="stMetric"] {
      background: #fffdf9; border: 1px solid #eadbc8; border-left: 5px solid #c2693f;
      border-radius: 14px; padding: .9rem 1rem; box-shadow: 0 2px 8px rgba(120, 80, 40, .08);
    }
    [data-testid="stMetricValue"] {color: #a9552f; font-weight: 700;}
    [data-testid="stVerticalBlockBorderWrapper"] {
      border-radius: 14px; background: #fffdf9; border-color: #eadbc8;
      box-shadow: 0 2px 8px rgba(120, 80, 40, .06);
    }
    .stTabs [data-baseweb="tab-list"] {gap: .4rem;}
    .stTabs [data-baseweb="tab"] {
      background: #f1e4d3; border-radius: 12px 12px 0 0; padding: .5rem 1rem;
    }
    .stTabs [data-baseweb="tab"] p {color: #6b5444;}
    .stTabs [aria-selected="true"] {background: #c2693f;}
    .stTabs [aria-selected="true"] p {color: #ffffff;}
    .stTabs [data-baseweb="tab-highlight"] {display: none;}
    .stButton > button, [data-testid="stFormSubmitButton"] > button {
      border-radius: 10px; font-weight: 600; border: 1px solid #d9c3a8;
      color: #5a4336; background: #fffdf9;
    }
    button[kind="primary"], button[kind="primaryFormSubmit"],
    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
      background-color: #c2693f !important; border-color: #c2693f !important;
      color: #ffffff !important;
    }
    [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {
      background: #f6e7d4; color: #4a3428;
    }
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
tab_plan, tab_subjects, tab_add, tab_progress, tab_week, tab_check, tab_perf, tab_pomo = st.tabs(["✨ Today's plan", "📖 My subjects", "➕ Add a subject", "📊 Progress", "📅 Week plan", "✅ Checklist", "🏆 Performance", "⏱️ Pomodoro"])
with tab_perf:
    st.subheader("Your weekly performance")
    goal_hours = st.number_input("Your daily study goal (hours)", min_value=0.25, max_value=24.0, value=2.0, step=0.25, key="goal_hours")
    goal_minutes = goal_hours * 60
    perf_days = [date.today() - timedelta(days=n) for n in range(6, -1, -1)]
    perf_minutes = []
    subject_minutes = {}
    for perf_day in perf_days:
        perf_key = perf_day.strftime(DATE_FORMAT)
        day_sum = 0
        for s_idx, s in enumerate(subjects):
            logs = s.get("studied", {})
            if isinstance(logs, dict):
                try:
                    logged = int(logs.get(perf_key, 0))
                except (ValueError, TypeError):
                    logged = 0
                day_sum += logged
                subject_minutes[s_idx] = subject_minutes.get(s_idx, 0) + logged
        perf_minutes.append(day_sum)

    goal_days_met = sum(1 for m in perf_minutes if m >= goal_minutes)
    avg_completion = sum(min(m / goal_minutes, 1.0) for m in perf_minutes) / 7
    score = round(avg_completion * 100)
    if score >= 85:
        verdict = "🌟 Excellent week! You stayed on track."
    elif score >= 60:
        verdict = "👍 Good week. A little more consistency will push you higher."
    elif score >= 30:
        verdict = "🙂 You're getting there. Try to study a bit every day."
    else:
        verdict = "🚀 Just getting started. Log your study time to build momentum."

    perf1, perf2, perf3 = st.columns(3)
    perf1.metric("Score", f"{score}/100")
    perf2.metric("Goal met", f"{goal_days_met} / 7 days")
    perf3.metric("Avg per day", f"{sum(perf_minutes) / 7 / 60:.1f} h")
    st.progress(score / 100)
    st.info(verdict)
    st.bar_chart(
        [{"Day": d.strftime("%m-%d %a"), "Minutes": m} for d, m in zip(perf_days, perf_minutes)],
        x="Day",
        y="Minutes",
    )

    st.markdown("*Needs attention*")
    attention = []
    for s_idx, s in enumerate(subjects):
        left_days = safe_days_left(s)
        week_mins = subject_minutes.get(s_idx, 0)
        if 0 <= left_days <= 7 and week_mins < 60 and not is_resting(s):
            attention.append((left_days, s.get("name", "Unnamed"), week_mins))
    if attention:
        for left_days, subject_name, week_mins in sorted(attention):
            when = "today" if left_days == 0 else f"in {left_days} day(s)"
            st.warning(f"{subject_name}: exam {when}, only {week_mins} min studied this week.")
    else:
        st.success("No exam in the next 7 days is being neglected. Nice!")
with tab_check:
    st.subheader("Today's checklist")
    check_day = date.today().strftime(DATE_FORMAT)
    check_items = sorted(plan_items, key=lambda item: item[1])
    if not check_items:
        st.info("Nothing to check off yet. Add a subject in the *Add a subject* tab.")
    else:
        done_total = sum(
            1 for subject_item, _ in check_items
            if isinstance(subject_item.get("done"), dict) and subject_item["done"].get(check_day)
        )
        st.progress(done_total / len(check_items))
        st.caption(f"{done_total} of {len(check_items)} done today")
        for n, (check_subject, check_left) in enumerate(check_items):
            done_data = check_subject.get("done", {})
            already_done = isinstance(done_data, dict) and bool(done_data.get(check_day))
            hint = "exam today" if check_left == 0 else f"{check_left} day(s) to exam"
            ticked_now = st.checkbox(
                f"{check_subject.get('name', 'Unnamed')} · {hint}",
                value=already_done,
                key=f"check_{n}{check_day}{int(already_done)}",
            )
            if ticked_now != already_done:
                if not isinstance(check_subject.get("done"), dict):
                    check_subject["done"] = {}
                check_subject["done"][check_day] = ticked_now
                save_data(subjects)
                st.rerun()
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
                    today_key = date.today().strftime(DATE_FORMAT)
                    done_map = subject.get("done", {})
                    is_done = isinstance(done_map, dict) and bool(done_map.get(today_key))
                    ticked = st.checkbox("✅ Done for today", value=is_done, key=f"done_{idx}{today_key}{int(is_done)}")
                    if ticked != is_done:
                        for s in subjects:
                            if s is subject:
                                if not isinstance(s.get("done"), dict):
                                    s["done"] = {}
                                s["done"][today_key] = ticked
                        save_data(subjects)
                        st.rerun()
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
    if "quick_msg" in st.session_state:
        st.success(st.session_state.pop("quick_msg"))
    st.subheader("Quick add: tick your subjects")
    common_subjects = [
        "Mathematics", "English", "Science", "Physics", "Chemistry", "Biology",
        "History", "Geography", "Computer Science", "Economics",
        "Business Studies", "Psychology", "Art", "Music",
        "Second Language", "Physical Education",
    ]
    existing_names = {s.get("name", "").strip().lower() for s in subjects}
    quick_options = [n for n in common_subjects if n.lower() not in existing_names]
    picked = []
    if quick_options:
        quick_cols = st.columns(3)
        for q_idx, q_name in enumerate(quick_options):
            if quick_cols[q_idx % 3].checkbox(q_name, key=f"quick_{q_name}"):
                picked.append(q_name)
    else:
        st.caption("All the quick-pick subjects are already added.")
    if picked:
        with st.form("quick_add_form"):
            st.write("Set an exam date and difficulty for each subject you ticked:")
            quick_inputs = []
            for q_name in picked:
                qc1, qc2 = st.columns(2)
                q_date = qc1.date_input(f"{q_name}: exam date", min_value=today, value=today + timedelta(days=14), key=f"qdate_{q_name}")
                q_diff = qc2.slider(f"{q_name}: difficulty", min_value=1, max_value=5, value=3, key=f"qdiff_{q_name}")
                quick_inputs.append((q_name, q_date, q_diff))
            quick_submit = st.form_submit_button("Add ticked subjects", type="primary", use_container_width=True)
        if quick_submit:
            for q_name, q_date, q_diff in quick_inputs:
                subjects.append({
                    "name": q_name,
                    "exam_date": q_date.strftime(DATE_FORMAT),
                    "difficulty": q_diff,
                })
            save_data(subjects)
            st.session_state.subjects = subjects
            st.session_state["quick_msg"] = f"Added {len(quick_inputs)} subject(s)!"
            st.rerun()
    st.divider()
    st.subheader("Or add a custom subject")
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
st.divider()
st.subheader("Topic checklists")
if not subjects:
    st.info("Add a subject first, then add topics to it here.")
for t_idx, t_subject in enumerate(sorted(subjects, key=safe_days_left)):
    topics = t_subject.get("topics", [])
    if not isinstance(topics, list):
        topics = []
    done_topics = sum(1 for tp in topics if isinstance(tp, dict) and tp.get("done"))
    with st.expander(f"📝 {t_subject.get('name', 'Unnamed')}"):
        st.caption(f"{done_topics} of {len(topics)} topics done")
        for p_idx, topic in enumerate(topics):
            if not isinstance(topic, dict):
                continue
            t_done = bool(topic.get("done"))
            t_cols = st.columns([5, 1])
            t_ticked = t_cols[0].checkbox(topic.get("title", "Topic"), value=t_done, key=f"topic_{t_idx}{p_idx}{int(t_done)}")
            if t_ticked != t_done:
                topic["done"] = t_ticked
                save_data(subjects)
                st.rerun()
            if t_cols[1].button("🗑️", key=f"topicdel_{t_idx}_{p_idx}"):
                topics.pop(p_idx)
                save_data(subjects)
                st.rerun()
    with st.form(f"topic_form_{t_idx}", clear_on_submit=True):
        new_topic = st.text_input("New topic", placeholder="e.g. Chapter 3 - Algebra", key=f"topic_new_{t_idx}")
        add_topic = st.form_submit_button("Add topic")
    if add_topic and new_topic.strip():
        if not isinstance(t_subject.get("topics"), list):
            t_subject["topics"] = []
        t_subject["topics"].append({"title": new_topic.strip(), "done": False})
        save_data(subjects)
        st.rerun()
with tab_pomo:
    st.subheader("Pomodoro timer")
    if "pomo_msg" in st.session_state:
        st.success(st.session_state.pop("pomo_msg"))
    if not subjects:
        st.info("Add a subject first, then you can study with the timer here.")
    else:
        state = st.session_state
        pomo_c1, pomo_c2, pomo_c3 = st.columns(3)
        focus_min = pomo_c1.number_input("Focus (min)", min_value=1, max_value=120, value=25, step=1, key="pomo_focus")
        break_min = pomo_c2.number_input("Break (min)", min_value=1, max_value=60, value=5, step=1, key="pomo_break")
        pomo_pick = pomo_c3.selectbox("Subject", range(len(subjects)), format_func=lambda i: subjects[i].get("name", "Unnamed"))
        state.setdefault("pomo_mode", "focus")
        state.setdefault("pomo_running", False)
        state.setdefault("pomo_left", None)
        state.setdefault("pomo_end", 0.0)
        state.setdefault("pomo_planned", 25)
        state.setdefault("pomo_count", 0)

        def pomo_full(which):
            return (int(focus_min) if which == "focus" else int(break_min)) * 60

        @st.fragment(run_every=1 if state["pomo_running"] else None)
        def pomodoro_clock():
            mode = state["pomo_mode"]
            if state["pomo_running"]:
                left = max(0, int(round(state["pomo_end"] - datetime.now().timestamp())))
            elif state["pomo_left"] is not None:
                left = state["pomo_left"]
            else:
                left = pomo_full(mode)

            if state["pomo_running"] and left <= 0:
                if mode == "focus":
                    target = subjects[pomo_pick]
                    if not isinstance(target.get("studied"), dict):
                        target["studied"] = {}
                    day_now = date.today().strftime(DATE_FORMAT)
                    target["studied"][day_now] = target["studied"].get(day_now, 0) + int(state["pomo_planned"])
                    save_data(subjects)
                    state["pomo_count"] += 1
                    state["pomo_mode"] = "break"
                    state["pomo_running"] = True
                    state["pomo_left"] = None
                    state["pomo_end"] = datetime.now().timestamp() + pomo_full("break")
                    state["pomo_msg"] = f"🎉 Focus session done! {int(state['pomo_planned'])} min logged for {target.get('name', 'subject')}. Break time!"
                else:
                    state["pomo_mode"] = "focus"
                    state["pomo_running"] = False
                    state["pomo_left"] = None
                    state["pomo_msg"] = "☕ Break over. Ready for the next focus session?"
                st.rerun()

            total = max(pomo_full(mode), 1)
            minutes_left, seconds_left = divmod(left, 60)
            title = "🎯 Focus time" if mode == "focus" else "☕ Break time"
            st.markdown(
                f"<div style='text-align:center;padding:10px'>"
                f"<div style='font-weight:700;color:#6c5ce7;font-size:1.2rem'>{title}</div>"
                f"<div style='font-size:4rem;font-weight:800;color:#29234b'>{minutes_left:02d}:{seconds_left:02d}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.progress(min(max(1 - left / total, 0.0), 1.0))
            b1, b2, b3 = st.columns(3)
            if b1.button("▶️ Start", use_container_width=True, disabled=state["pomo_running"]):
                if state["pomo_left"] is None:
                    state["pomo_planned"] = pomo_full(mode) // 60
                state["pomo_end"] = datetime.now().timestamp() + left
                state["pomo_running"] = True
                st.rerun()
            if b2.button("⏸️ Pause", use_container_width=True, disabled=not state["pomo_running"]):
                state["pomo_left"] = left
                state["pomo_running"] = False
                st.rerun()
            if b3.button("↺ Reset", use_container_width=True):
                state["pomo_mode"] = "focus"
                state["pomo_running"] = False
                state["pomo_left"] = None
                st.rerun()

        pomodoro_clock()
        st.caption(f"Focus sessions completed: {state['pomo_count']}. Each finished focus session is logged to the subject you picked. Keep this page open while the timer runs.")
