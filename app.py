from __future__ import annotations

import calendar
import html
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from database import CATEGORIES, PRIORITIES, STATUSES, TaskStore
from legal import LEGAL_VERSION, can_accept_for_adult_release
from planner import breakdown_for, build_day_plan


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "focusflow.db"
LEGAL_VERSION_SETTING = "legal_accepted_version"
st.set_page_config(page_title="FocusFlow", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

PALETTES = {
    "Dark": {"bg": "#0d111c", "panel": "#151b2a", "panel2": "#1c2435", "text": "#f3f5fb", "muted": "#9aa6bc", "line": "#29334a", "accent": "#9b8cff", "mint": "#65e0c1"},
    "Light": {"bg": "#f4f6fb", "panel": "#ffffff", "panel2": "#f0f2fa", "text": "#20253a", "muted": "#69738a", "line": "#e3e7f0", "accent": "#6654e8", "mint": "#149f83"},
}


def read_policy(filename: str) -> str:
    content = (APP_DIR / filename).read_text(encoding="utf-8")
    return content.replace("TERMS_OF_USE.md", "#terms-of-use").replace("PRIVACY_POLICY.md", "#privacy-policy")


@st.dialog("Before you start using FocusFlow", width="large", dismissible=False)
def first_use_consent(store: TaskStore) -> None:
    st.write("Please review both documents. This release is only for people aged 18 or older.")
    st.warning("Under-18 access is not available. FocusFlow does not yet verify parental or guardian consent; the age confirmation below is a self-attestation only.")
    with st.expander("Read the Terms of Use", expanded=True):
        st.markdown(read_policy("TERMS_OF_USE.md"))
    terms_agreed = st.checkbox("I agree to the FocusFlow Terms of Use", key=f"terms_consent_{LEGAL_VERSION}")
    with st.expander("Read the Privacy Policy"):
        st.markdown(read_policy("PRIVACY_POLICY.md"))
    privacy_acknowledged = st.checkbox("I have read and acknowledge the FocusFlow Privacy Policy", key=f"privacy_consent_{LEGAL_VERSION}")
    adult_confirmed = st.checkbox("I confirm that I am 18 years of age or older", key=f"adult_consent_{LEGAL_VERSION}")
    st.caption("Your acceptance record is saved on this device. Do not continue if you do not agree.")
    if st.button("Agree and continue", type="primary", use_container_width=True, disabled=not can_accept_for_adult_release(terms_agreed, privacy_acknowledged, adult_confirmed)):
        store.set_setting(LEGAL_VERSION_SETTING, LEGAL_VERSION)
        store.set_setting("legal_accepted_at", datetime.now().astimezone().isoformat())
        store.set_setting("adult_age_self_attested", "true")
        st.rerun()


def clear_policy_page() -> None:
    st.session_state["legal_page"] = None


def apply_theme(name: str) -> dict[str, str]:
    c = PALETTES[name]
    st.markdown(f"""<style>
      :root {{ color-scheme: {'dark' if name == 'Dark' else 'light'}; --primary-color: {c['accent']} !important; --st-primary-color: {c['accent']} !important; --background-color: {c['bg']}; --secondary-background-color: {c['panel']}; --text-color: {c['text']}; }}
      html, body, [data-testid="stAppViewContainer"], .stApp {{ background: {c['bg']} !important; color: {c['text']} !important; font-family: 'Segoe UI', Aptos, sans-serif; }}
      [data-testid="stSidebar"] {{ background: {c['panel']} !important; border-right: 1px solid {c['line']}; }}
      [data-testid="stHeader"] {{ background: transparent !important; }}
      /* Keep Streamlit's sidebar reopen control available when the drawer is collapsed. */
      [data-testid="stMainMenu"], [data-testid="stDeployButton"], #MainMenu {{ display: none !important; }}
      h1,h2,h3,h4,p, label, [data-testid="stMarkdownContainer"] {{ color: {c['text']}; }}
      h1,h2,h3 {{ letter-spacing: -.035em; }}
      [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {c['muted']} !important; }}
      [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] > div {{ background: {c['panel2']} !important; color: {c['text']} !important; border-color: {c['line']} !important; }}
      input::placeholder, textarea::placeholder {{ color: {c['muted']} !important; opacity:1; }}
      [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{ background: {c['panel']} !important; color: {c['text']} !important; }}
      [role="option"] {{ color: {c['text']} !important; }} [role="option"]:hover {{ background: {c['panel2']} !important; }}
      [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{ color: {c['text']} !important; }}
      [data-baseweb="radio"] > div:first-child {{ border-color:{c['accent']} !important; }}
      [data-baseweb="radio"][aria-checked="true"] > div:first-child > div {{ background:{c['accent']} !important; }}
      [data-testid="stSlider"] [role="slider"] {{ border-color:{c['accent']} !important; background:{c['accent']} !important; }}
      [data-testid="stExpander"] details, [data-testid="stExpander"] summary {{ background:{c['panel']} !important; color:{c['text']} !important; border-color:{c['line']} !important; }}
      [data-testid="stExpander"] summary p {{ color:{c['text']} !important; }}
      [data-testid="stProgressBar"] > div > div {{ background: {c['accent']} !important; }}
      [data-testid="stAlert"] {{ background: {c['panel']} !important; color: {c['text']} !important; border-color: {c['line']} !important; }}
      .hero {{ background: linear-gradient(115deg, {c['panel']} 0%, {c['panel2']} 100%); border: 1px solid {c['line']}; padding: 26px 30px; border-radius: 22px; margin: 6px 0 22px; }}
      .eyebrow {{ color: {c['accent']}; text-transform: uppercase; letter-spacing: .14em; font-size: 11px; font-weight: 700; }}
      .hero h1 {{ margin: 8px 0 4px; font-size: 34px; }} .hero p {{ color:{c['muted']}; margin:0; }}
      .metric-card {{ background:{c['panel']}; border:1px solid {c['line']}; border-radius:17px; padding:17px 19px; min-height:112px; }}
      .metric-label {{ color:{c['muted']}; font-size:12px; font-weight:600; }} .metric-value {{ font-family:'Manrope'; color:{c['text']}; font-weight:800; font-size:29px; margin:5px 0 1px; }} .metric-foot {{ color:{c['muted']}; font-size:11px; }}
      .section-kicker {{ font-size:12px; letter-spacing:.11em; color:{c['muted']}; font-weight:700; text-transform:uppercase; margin:12px 0 7px; }}
      .task-card {{ background:{c['panel']}; border:1px solid {c['line']}; border-radius:14px; padding:14px 15px; margin:8px 0; }}
      .task-title {{ font-weight:700; color:{c['text']}; font-size:14px; }} .task-meta {{ color:{c['muted']}; font-size:11px; margin-top:7px; }}
      div[data-testid="stMetric"] {{ background:{c['panel']}; border:1px solid {c['line']}; padding:14px 16px; border-radius:16px; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }}
      @media (max-width: 900px) {{
        .block-container {{ padding: 1.2rem 1rem 2rem; }}
        [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: .75rem; }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{ flex: 1 1 44% !important; min-width: min(100%, 250px) !important; }}
        .hero {{ padding: 22px 20px; }} .hero h1 {{ font-size: clamp(24px, 6vw, 34px); }}
      }}
      @media (max-width: 560px) {{
        .block-container {{ padding: .8rem .7rem 1.5rem; }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{ flex-basis: 100% !important; min-width: 100% !important; }}
        div[data-testid="stMetric"] {{ padding: 11px 12px; }}
        .metric-card {{ min-height: 88px; }}
        .task-card {{ padding: 12px; }}
        h1 {{ font-size: 1.7rem !important; }}
      }}
      .stButton button, .stFormSubmitButton button {{ border-radius:10px; background: {c['panel2']}; color:{c['text']}; border-color:{c['line']}; }}
      .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {{ background:{c['accent']}; color:#fff; border-color:{c['accent']}; }}
      [data-testid="stContainer"] {{ border-color: {c['line']} !important; }}
    </style>""", unsafe_allow_html=True)
    return c


def greeting() -> str:
    hour = datetime.now().hour
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"


def metric(label: str, value: str, foot: str, icon: str) -> None:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{icon} &nbsp;{label}</div><div class="metric-value">{value}</div><div class="metric-foot">{foot}</div></div>', unsafe_allow_html=True)


def task_frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce").dt.date
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df


def task_line(task: dict, compact: bool = False) -> None:
    due = task.get("due_date") or "No deadline"
    due_text = due
    # Build the day without %-d, which Windows' strftime does not support.
    if due != "No deadline":
        parsed = date.fromisoformat(due)
        due_text = parsed.strftime("%b") + f" {parsed.day}"
    st.markdown(f'<div class="task-card"><div class="task-title">{html.escape(task["title"])}</div><div class="task-meta">{html.escape(task["category"])} &nbsp;·&nbsp; {html.escape(task["priority"])} &nbsp;·&nbsp; {html.escape(due_text)} &nbsp;·&nbsp; {task["estimated_minutes"]} min</div></div>', unsafe_allow_html=True)


def task_list_print_button(tasks: list[dict], colors: dict[str, str]) -> None:
    """Print the currently filtered tasks together as one clean checklist."""
    printed_tasks = []
    for task in tasks:
        due = task.get("due_date") or "No deadline"
        printed_tasks.append(
            "<article><div class='heading'><b>□ &nbsp;" + html.escape(task["title"]) + "</b>"
            + "<span>" + html.escape(task["status"]) + "</span></div>"
            + "<p>" + html.escape(task["category"]) + " · " + html.escape(task["priority"])
            + " · " + html.escape(due) + " · " + str(int(task["estimated_minutes"])) + " min</p>"
            + (f"<p class='notes'>{html.escape(task['description'])}</p>" if task.get("description") else "")
            + "</article>"
        )
    content = "".join(printed_tasks) or "<p>No tasks match the current filters.</p>"
    document = f"""<!doctype html><html><head><meta charset='utf-8'><style>
      body{{margin:0;font-family:Segoe UI,Arial,sans-serif;color:{colors['text']}}}button{{height:40px;border:1px solid {colors['line']};border-radius:9px;background:{colors['panel2']};color:{colors['text']};padding:0 18px;font:600 13px Segoe UI,Arial;cursor:pointer}}
      #print-card{{display:none}}h1{{font-size:25px;margin:0 0 5px}}.sub{{color:#68738c;margin:0 0 18px}}article{{padding:12px 0;border-bottom:1px solid #dce1ec}}.heading{{display:flex;justify-content:space-between;gap:15px}}article p{{margin:5px 0;color:#59647a;font-size:13px}}article .notes{{white-space:pre-wrap;color:#374052}}.empty{{color:#68738c}}
      @media print{{button{{display:none!important}}#print-card{{display:block!important}}body{{padding:24px}}}}
    </style></head><body><button onclick='window.print()'>▤ Print task list ({len(tasks)})</button><main id='print-card'><h1>FocusFlow task list</h1><p class='sub'>Printed {date.today().isoformat()} · {len(tasks)} task{'s' if len(tasks) != 1 else ''}</p>{content}</main></body></html>"""
    components.html(document, height=43, scrolling=False)


@st.dialog("Add a task")
def add_task_dialog(store: TaskStore, initial_due: date | None = None) -> None:
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Task name *", placeholder="e.g. Finish database assignment")
        description = st.text_area("Notes", placeholder="A little context helps future you.", height=75)
        left, right = st.columns(2)
        category = left.selectbox("Category", CATEGORIES)
        priority = right.selectbox("Priority", PRIORITIES, index=1)
        due = left.date_input("Deadline", value=initial_due or (date.today() + timedelta(days=1)), key=f"add_due_{initial_due or 'default'}")
        duration = right.number_input("Estimated minutes", min_value=5, max_value=1440, value=45, step=5)
        permanent = st.checkbox("Permanent daily task", help="Keep this task in your everyday list. Its status resets to To do each new day; previous days are saved.")
        recurring = "Never" if permanent else st.selectbox("Repeat", ["Never", "Daily", "Weekly", "Monthly"])
        submitted = st.form_submit_button("Create task", type="primary", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Give your task a name first.")
            else:
                task_date = date.today() if permanent else due
                store.create(title.strip(), description.strip(), category, priority, task_date.isoformat(), int(duration), "To do", recurring, permanent)
                st.success("Task added to your flow.")
                st.rerun()


@st.dialog("Edit task")
def edit_task_dialog(store: TaskStore, task: dict) -> None:
    with st.form(f"task_edit_dialog_{task['id']}"):
        title = st.text_input("Task name", value=task["title"])
        notes = st.text_area("Notes", value=task["description"])
        first, second = st.columns(2)
        category = first.selectbox("Category", CATEGORIES, index=CATEGORIES.index(task["category"]))
        priority = second.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(task["priority"]))
        has_deadline = st.checkbox("Has a deadline", value=bool(task["due_date"]))
        due = st.date_input("Deadline", value=date.fromisoformat(task["due_date"]) if task["due_date"] else date.today(), disabled=not has_deadline)
        last, repeat_col = st.columns(2)
        duration = last.number_input("Estimated focus time (minutes)", min_value=5, max_value=1440, value=int(task["estimated_minutes"]), step=5)
        permanent = st.checkbox("Permanent daily task", value=bool(task.get("permanent", 0)), help="Keep this task in your everyday list. Its status resets to To do each new day; previous days are saved.")
        recurring = "Never" if permanent else repeat_col.selectbox("Repeat", ["Never", "Daily", "Weekly", "Monthly"], index=["Never", "Daily", "Weekly", "Monthly"].index(task["recurring"]))
        if st.form_submit_button("Save changes", type="primary", use_container_width=True):
            if not title.strip():
                st.error("Give your task a name first.")
            else:
                task_date = date.today() if permanent else (due.isoformat() if has_deadline else None)
                store.update(task["id"], title.strip(), notes.strip(), category, priority, task_date, int(duration), recurring, permanent)
                st.success("Task updated.")
                st.rerun()


def render_calendar(rows: list[dict], colors: dict[str, str], store: TaskStore) -> None:
    if "calendar_month" not in st.session_state:
        st.session_state["calendar_month"] = date.today().replace(day=1)
    month_anchor = st.session_state["calendar_month"]
    prev_col, heading_col, next_col = st.columns([1, 4, 1])
    with prev_col:
        if st.button("← Previous", key="calendar_prev"):
            year, month = month_anchor.year, month_anchor.month - 1
            st.session_state.calendar_month = date(year - (month == 0), month or 12, 1)
            st.session_state.calendar_selected_date = st.session_state.calendar_month
            st.rerun()
    with heading_col:
        st.markdown(f"### {month_anchor.strftime('%B %Y')}")
    with next_col:
        if st.button("Next →", key="calendar_next"):
            year, month = month_anchor.year, month_anchor.month + 1
            st.session_state.calendar_month = date(year + (month == 13), month if month < 13 else 1, 1)
            st.session_state.calendar_selected_date = st.session_state.calendar_month
            st.rerun()

    for col, day_name in zip(st.columns(7), ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
        col.markdown(f"<div class='section-kicker'>{day_name[:3]}</div>", unsafe_allow_html=True)
    events: dict[str, list[dict]] = {}
    for task in rows:
        if task.get("due_date"):
            events.setdefault(task["due_date"], []).append(task)
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month_anchor.year, month_anchor.month):
        cols = st.columns(7, gap="small")
        for col, day_date in zip(cols, week):
            with col:
                day_events = events.get(day_date.isoformat(), [])
                event_lines = "".join(f"<div style='font-size:10px;color:{colors['muted']};overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>• {html.escape(task['title'])}</div>" for task in day_events[:3])
                extra = f"<div style='font-size:10px;color:{colors['muted']}'>+{len(day_events) - 3} more</div>" if len(day_events) > 3 else ""
                is_selected = st.session_state.get("calendar_selected_date", date.today()) == day_date
                if st.button(str(day_date.day), key=f"calendar_date_{day_date.isoformat()}", help=f"Choose {day_date.strftime('%B')} {day_date.day}", type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state.calendar_selected_date = day_date
                    st.rerun()
                st.markdown(f"<div style='background:{colors['panel']};border:1px solid {colors['line']};border-radius:10px;padding:5px;min-height:38px'>{event_lines}{extra}</div>", unsafe_allow_html=True)

    selected = st.session_state.get("calendar_selected_date", date.today())
    selected_tasks = events.get(selected.isoformat(), [])
    st.markdown(f"### {selected.strftime('%A, %B')} {selected.day}")
    if selected_tasks:
        for task in selected_tasks:
            st.markdown(f"• **{html.escape(task['title'])}** — {task['status']} · {task['estimated_minutes']} min")
    else:
        st.caption("No tasks due on this day yet.")
    if st.button(f"＋ Add task for {selected.strftime('%b')} {selected.day}", type="primary", key="calendar_add_selected"):
        add_task_dialog(store, selected)

    overdue_tasks = [task for task in rows if task["status"] != "Done" and task["due_date"] and task["due_date"] < date.today().isoformat()]
    st.markdown("### Past-due carryovers")
    if not overdue_tasks:
        st.caption("No unfinished tasks from earlier days.")
    else:
        st.caption("They stay on their original dates above. Move an unfinished task to today when you want to reschedule it.")
        for task in overdue_tasks:
            old_date = date.fromisoformat(task["due_date"])
            left, right = st.columns([4, 1])
            left.markdown(f"**{html.escape(task['title'])}** · was due {old_date.strftime('%b')} {old_date.day} · {task['estimated_minutes']} min")
            if right.button("Move to today", key=f"carry_{task['id']}"):
                store.update_due_date(task["id"], date.today().isoformat())
                st.rerun()


def render_planner(rows: list[dict], colors: dict[str, str], store: TaskStore) -> None:
    st.markdown("## Plan your day")
    st.caption("A free, offline plan ranked by priority and deadline. You choose the time budget; FocusFlow suggests an order.")
    left, right = st.columns([1, 1])
    with left:
        plan_date = st.date_input("Plan date", value=date.today(), key="plan_date")
        capacity = st.slider("Available focus time", min_value=30, max_value=720, value=240, step=15, format="%d min")
    with right:
        start_at = st.time_input("Start at", value=time(9, 0), step=timedelta(minutes=15))
        break_length = st.slider("Break between tasks", min_value=0, max_value=30, value=10, step=5, format="%d min")

    active = [task for task in rows if task["status"] != "Done"]
    late = [task for task in active if task["due_date"] and task["due_date"] < date.today().isoformat()]
    due_today = [task for task in active if task["due_date"] == date.today().isoformat()]
    if late:
        st.warning(f"Local reminder: {len(late)} task{'s are' if len(late) != 1 else ' is'} overdue. Review these in My tasks.")
    elif due_today:
        st.info(f"Local reminder: {len(due_today)} task{'s are' if len(due_today) != 1 else ' is'} due today.")

    schedule = build_day_plan(active, plan_date, capacity, start_at, break_length)
    st.markdown("### Suggested schedule")
    if not schedule:
        st.info("No tasks fit that time budget. Increase your available time or shorten a task estimate.")
    else:
        used = sum(item["minutes"] for item in schedule)
        st.progress(min(1.0, used / capacity), text=f"{used} of {capacity} focus minutes planned")
        for item in schedule:
            task = item["task"]
            start_label = datetime.combine(plan_date, item["start"]).strftime("%I:%M %p").lstrip("0")
            end_label = datetime.combine(plan_date, item["end"]).strftime("%I:%M %p").lstrip("0")
            st.markdown(f"<div class='task-card'><b>{start_label} – {end_label}</b> &nbsp;·&nbsp; {html.escape(task['priority'])}<br><span class='task-meta'>{html.escape(task['title'])} · {item['minutes']} min · {html.escape(task['category'])}</span></div>", unsafe_allow_html=True)

    st.markdown("### Quick task breakdowns")
    st.caption("Starter steps are generated from simple local templates. Nothing is sent to an AI service.")
    candidates = sorted(active, key=lambda task: (-PRIORITIES.index(task["priority"]), task["due_date"] or "9999-12-31"))
    if not candidates:
        st.caption("Add a task to see a practical starter checklist.")
    for task in candidates[:8]:
        title_col, edit_col = st.columns([5, 1])
        title_col.markdown(f"**{html.escape(task['title'])}** · {task['estimated_minutes']} min")
        if edit_col.button("✎ Edit", key=f"planner_edit_{task['id']}", use_container_width=True):
            edit_task_dialog(store, task)
        with st.expander(f"Break down: {task['title']}"):
            for index, step in enumerate(breakdown_for(task)):
                st.checkbox(step, key=f"breakdown_{task['id']}_{index}")


def main() -> None:
    store = TaskStore(DB_PATH)
    if (
        store.get_setting(LEGAL_VERSION_SETTING) != LEGAL_VERSION
        or store.get_setting("adult_age_self_attested") != "true"
    ):
        apply_theme(st.session_state.get("theme", "Dark"))
        first_use_consent(store)
        st.stop()
    store.reset_permanent_tasks()
    with st.sidebar:
        st.markdown("<div style='font-size:13px;color:#9aa6bc'>✦ &nbsp;YOUR PERSONAL WORKSPACE</div>", unsafe_allow_html=True)
        st.markdown("# 🎯 FocusFlow")
        st.caption("Make room for what matters.")
        page = st.radio("Navigate", ["Overview", "My tasks", "Calendar", "Plan my day", "Board"], label_visibility="collapsed", key="navigation_page", on_change=clear_policy_page)
        st.divider()
        theme = st.radio("Appearance", ["Dark", "Light"], horizontal=True, label_visibility="collapsed", index=0 if st.session_state.get("theme", "Dark") == "Dark" else 1)
        st.session_state["theme"] = theme
        st.caption("Your tasks stay on this device.")
        st.divider()
        legal_terms_col, legal_privacy_col = st.columns(2)
        if legal_terms_col.button("Terms of Use", use_container_width=True):
            st.session_state["legal_page"] = "Terms of Use"
            st.rerun()
        if legal_privacy_col.button("Privacy Policy", use_container_width=True):
            st.session_state["legal_page"] = "Privacy Policy"
            st.rerun()
    page = st.session_state.get("legal_page") or page
    colors = apply_theme(theme)
    rows = store.list_all()
    df = task_frame(rows)
    today = date.today()
    active = [t for t in rows if t["status"] != "Done"]
    completed = [t for t in rows if t["status"] == "Done"]
    due_today = [t for t in active if t["due_date"] == today.isoformat()]
    overdue = [t for t in active if t["due_date"] and t["due_date"] < today.isoformat()]
    if page == "Terms of Use":
        st.markdown(read_policy("TERMS_OF_USE.md"))
    elif page == "Privacy Policy":
        st.markdown(read_policy("PRIVACY_POLICY.md"))
    elif page == "Overview":
        st.markdown(f'<div class="hero"><div class="eyebrow">{today.strftime("%A, %B ")} {today.day}</div><h1>{greeting()}, let’s find your focus.</h1><p>A clear plan makes a lighter day. You’ve got this.</p></div>', unsafe_allow_html=True)
        if overdue:
            st.warning(f"In-app reminder: {len(overdue)} overdue task{'s need' if len(overdue) != 1 else ' needs'} a quick review.")
        elif due_today:
            st.info(f"In-app reminder: {len(due_today)} task{'s are' if len(due_today) != 1 else ' is'} due today.")
        c1, c2, c3, c4 = st.columns(4)
        with c1: metric("Active tasks", str(len(active)), "Ready when you are", "◉")
        with c2: metric("Due today", str(len(due_today)), "A small step at a time", "◷")
        with c3: metric("Completed", str(len(completed)), "Things you’ve moved forward", "✓")
        with c4: metric("Overdue", str(len(overdue)), "Bring these back into view", "↗")
        st.write("")
        left, right = st.columns([1.45, 1])
        with left:
            st.markdown("### Your next steps")
            st.caption("The nearest deadlines, all in one place.")
            upcoming = sorted([t for t in active if t["due_date"]], key=lambda t: t["due_date"])
            if upcoming:
                for task in upcoming[:5]: task_line(task)
            else:
                st.info("No deadlines on the horizon. Add a task whenever you’re ready.")
        with right:
            st.markdown("### Where your time goes")
            if not df.empty:
                counts = df[df.status != "Done"].groupby("category").size().reset_index(name="Tasks")
                if len(counts):
                    fig = px.pie(counts, values="Tasks", names="category", hole=.68, color_discrete_sequence=[colors["accent"], colors["mint"], "#ffb86b", "#f27f98"])
                    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-.15, font=dict(color=colors["muted"], size=10)), margin=dict(t=4,b=4,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=colors["text"], height=225)
                    fig.update_traces(textinfo="none", marker=dict(line=dict(color=colors["panel"], width=3)))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Your category chart will appear as you add tasks.")
            else:
                st.info("Your category chart will appear as you add tasks.")
        st.markdown("### Progress at a glance")
        if rows:
            progress = len(completed) / len(rows)
            st.progress(progress, text=f"{len(completed)} of {len(rows)} tasks completed")
            if not df.empty:
                status_data = df.groupby("status").size().reindex(STATUSES, fill_value=0).reset_index(name="Tasks")
                bar = px.bar(status_data, x="status", y="Tasks", color="status", color_discrete_sequence=[colors["accent"], colors["mint"], "#ffb86b"])
                bar.update_layout(showlegend=False, margin=dict(t=5,b=5,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=colors["muted"], height=185, xaxis_title=None, yaxis_title=None)
                bar.update_xaxes(showgrid=False, zeroline=False); bar.update_yaxes(showgrid=True, gridcolor=colors["line"], zeroline=False)
                st.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("<div class='task-card'>✨ <b>Your workspace is ready.</b> Add your first task to see your momentum grow.</div>", unsafe_allow_html=True)
    elif page == "My tasks":
        title_col, action_col = st.columns([4, 1])
        with title_col:
            st.markdown("## My tasks")
            st.caption("Everything you’re working on, in one calm place.")
        with action_col:
            if st.button("＋ Add task", type="primary", use_container_width=True): add_task_dialog(store)
        search_col, cat_col, status_col = st.columns([2, 1, 1])
        query = search_col.text_input("Search tasks", placeholder="Search by name or notes…", label_visibility="collapsed")
        category_filter = cat_col.selectbox("Category", ["All categories", *CATEGORIES], label_visibility="collapsed")
        status_filter = status_col.selectbox("Status", ["All statuses", *STATUSES], label_visibility="collapsed")
        filtered = [t for t in rows if (not query or query.casefold() in (t["title"] + " " + t["description"]).casefold()) and (category_filter == "All categories" or t["category"] == category_filter) and (status_filter == "All statuses" or t["status"] == status_filter)]
        print_col, count_col = st.columns([1, 3])
        with print_col:
            task_list_print_button(filtered, colors)
        count_col.caption(f"Showing {len(filtered)} of {len(rows)} tasks · print includes this filtered list")
        if not filtered:
            st.info("No matching tasks. Try another filter or add something new.")
        for task in filtered:
            with st.container(border=True):
                a, b, c, d = st.columns([3.5, 1.2, 1.15, 1.0])
                a.markdown(f"**{task['title']}**")
                a.caption(f"{task['category']} · {task['priority']} · {task['estimated_minutes']} min" + (" · Every day" if task.get("permanent") else (f" · {task['due_date']}" if task["due_date"] else "")))
                if task["description"]: a.caption(task["description"])
                new_status = b.selectbox("Status", STATUSES, index=STATUSES.index(task["status"]), key=f"status_{task['id']}", label_visibility="collapsed")
                if new_status != task["status"]: store.update_status(task["id"], new_status); st.rerun()
                if c.button("✎ Edit", key=f"edit_{task['id']}", use_container_width=True): st.session_state[f"editing_{task['id']}"] = True
                if d.button("Delete", key=f"delete_{task['id']}", use_container_width=True): store.delete(task["id"]); st.rerun()
                if st.session_state.get(f"editing_{task['id']}"):
                    with st.form(f"edit_form_{task['id']}"):
                        new_title = st.text_input("Task name", task["title"])
                        new_description = st.text_area("Notes", task["description"])
                        e1, e2, e3 = st.columns(3)
                        new_cat = e1.selectbox("Category", CATEGORIES, index=CATEGORIES.index(task["category"]))
                        new_priority = e2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(task["priority"]))
                        new_due = e3.date_input("Deadline", value=date.fromisoformat(task["due_date"]) if task["due_date"] else date.today())
                        new_duration = st.number_input("Estimated minutes", min_value=5, max_value=1440, value=int(task["estimated_minutes"]), step=5)
                        new_permanent = st.checkbox("Permanent daily task", value=bool(task.get("permanent", 0)), help="Resets to To do each new day and stays in your everyday list.")
                        save, cancel = st.columns(2)
                        if save.form_submit_button("Save changes", type="primary"):
                            task_date = date.today().isoformat() if new_permanent else new_due.isoformat()
                            store.update(task["id"], new_title.strip(), new_description.strip(), new_cat, new_priority, task_date, int(new_duration), permanent=new_permanent); st.session_state.pop(f"editing_{task['id']}", None); st.rerun()
                        if cancel.form_submit_button("Cancel"):
                            st.session_state.pop(f"editing_{task['id']}", None); st.rerun()
    elif page == "Calendar":
        st.markdown("## Calendar")
        st.caption("Your deadlines, month by month.")
        render_calendar(rows, colors, store)
    elif page == "Plan my day":
        render_planner(rows, colors, store)
    else:
        st.markdown("## Your board")
        st.caption("Move work forward by changing its status in My tasks.")
        columns = st.columns(3)
        status_colors = {"To do": "#6f83ee", "In progress": "#e7a744", "Done": "#32a889"}
        priority_colors = {"Low": "#32a889", "Medium": "#e7a744", "High": "#e56776"}
        for col, status in zip(columns, STATUSES):
            bucket = [t for t in rows if t["status"] == status]
            with col:
                st.markdown(f"<div class='section-kicker'><span style='color:{status_colors[status]}'>{html.escape(status.upper())}</span> &nbsp; <span style='opacity:.65'>{len(bucket)}</span></div>", unsafe_allow_html=True)
                for task in bucket:
                    with st.container(border=True):
                        priority_color = priority_colors[task["priority"]]
                        st.markdown(f"<div style='border-left:4px solid {priority_color};padding:3px 0 3px 10px'><div style='font-weight:700;color:{colors['text']};font-size:14px'>{html.escape(task['title'])}</div><div style='font-size:11px;color:{colors['muted']};margin-top:7px'><span style='color:{status_colors[status]};font-weight:700'>{html.escape(task['category'])}</span> · <span style='color:{priority_color};font-weight:700'>{html.escape(task['priority'])}</span> · {task['estimated_minutes']} min</div></div>", unsafe_allow_html=True)
                        with st.expander("Task details", expanded=False):
                            st.markdown(f"**Focus time:** {int(task['estimated_minutes'])} minutes")
                            st.markdown(f"**Deadline:** {html.escape(task['due_date'] or 'No deadline')}")
                            st.markdown(f"**Notes:** {html.escape(task['description'] or 'No notes for this task.')}")
                if not bucket: st.caption("Nothing here yet")
    if page not in {"My tasks", "Terms of Use", "Privacy Policy"}:
        with st.sidebar:
            st.divider()
            if st.button("＋  Add a task", type="primary", use_container_width=True): add_task_dialog(store)


if __name__ == "__main__":
    main()
