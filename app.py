import streamlit as sm
import sqlite3
import hashlib
import smtplib
import random
import time
import re
import base64
import json
from datetime import datetime, date, time as dtime
import plotly.express as px
import plotly.graph_objects as go
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. STAGE CONFIGURATION ---
sm.set_page_config(
    page_title="AI Study Companion | Core Suite",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize User Preferences in Session State if not present
if "user_prefs" not in sm.session_state:
    sm.session_state.user_prefs = {
        "default_focus": 30,
        "short_break": 5,
        "long_break": 15,
        "daily_goal_hrs": 4.0,
        "remind_before": True,
        "remind_mins": 10,
        "theme": "Midnight OLED / Eye Protect",
        "font_size": "Medium",
        "layout_density": "Comfortable",
        "animations": True,
        "notify_reminders": True,
        "notify_deadlines": True,
        "notify_summary": False,
        "notify_sound": True
    }

# --- DYNAMIC CSS INJECTOR ENGINE ---
def inject_dynamic_css():
    """Generates dynamic CSS based on st.session_state.user_prefs and injects it into Streamlit."""
    prefs = sm.session_state.user_prefs

    # 1. Theme Color Mapping
    theme = prefs.get("theme", "Midnight OLED / Eye Protect")
    if theme == "Midnight OLED / Eye Protect":
        # Warm, ultra-low blue light palette designed for reduced eye strain
        bg_color = "#0B0E14"
        secondary_bg = "#121722"
        card_bg = "#1A202C"
        text_color = "#D1D5DB"
        border_color = "#2D3748"
        accent_color = "#38BDF8"
        kpi_title_color = "#9CA3AF"
    elif theme == "Dark SaaS":
        bg_color = "#0D1117"
        secondary_bg = "#161B22"
        card_bg = "#21262D"
        text_color = "#C9D1D9"
        border_color = "#30363D"
        accent_color = "#58A6FF"
        kpi_title_color = "#8B949E"
    elif theme == "Light Modern":
        bg_color = "#F8FAFC"
        secondary_bg = "#FFFFFF"
        card_bg = "#F1F5F9"
        text_color = "#0F172A"
        border_color = "#E2E8F0"
        accent_color = "#2563EB"
        kpi_title_color = "#64748B"
    else:  # High Contrast Dark
        bg_color = "#000000"
        secondary_bg = "#111111"
        card_bg = "#1E1E1E"
        text_color = "#FFFFFF"
        border_color = "#FFFFFF"
        accent_color = "#FACC15"
        kpi_title_color = "#E5E7EB"

    # 2. Font Size Scaling
    font_scale = prefs.get("font_size", "Medium")
    if font_scale == "Small":
        base_font = "13px"
        title_font = "1.5rem"
        timer_font = "3.0rem"
    elif font_scale == "Large":
        base_font = "17px"
        title_font = "2.2rem"
        timer_font = "4.5rem"
    else:  # Medium
        base_font = "15px"
        title_font = "1.8rem"
        timer_font = "3.8rem"

    # 3. Layout Density Padding
    density = prefs.get("layout_density", "Comfortable")
    if density == "Compact":
        container_padding = "1rem 1.5rem"
        card_padding = "12px"
        element_gap = "0.5rem"
    else:  # Comfortable
        container_padding = "2.5rem 3rem"
        card_padding = "20px"
        element_gap = "1rem"

    # 4. Interface Animations
    animations_enabled = prefs.get("animations", True)
    animation_css = "" if animations_enabled else "* { transition: none !important; animation: none !important; }"

    dynamic_css = f"""<style>
    /* Reset & Dynamic Theme Variables */
    .stApp, [data-testid="stSidebar"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-size: {base_font} !important;
    }}

    .main .block-container {{
        padding: {container_padding} !important;
        gap: {element_gap} !important;
    }}

    /* Dynamic Card Styles */
    .saas-card {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 12px;
        padding: {card_padding} !important;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    
    .kpi-title {{
        color: {kpi_title_color} !important;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .kpi-value {{
        color: {text_color} !important;
        font-size: {title_font} !important;
        font-weight: 700;
        margin-top: 4px;
    }}

    /* Interactive UI Controls */
    input, select, textarea, [data-baseweb="select"] {{
        background-color: {secondary_bg} !important;
        color: {text_color} !important;
        border-color: {border_color} !important;
    }}

    /* Buttons */
    .stButton>button[kind="primary"] {{
        background-color: #238636 !important;
        border-color: #2ea043 !important;
        color: #ffffff !important;
        font-weight: 600;
        border-radius: 8px;
    }}

    /* Timer Display */
    .timer-display {{
        font-size: {timer_font} !important;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: {accent_color} !important;
        text-align: center;
        letter-spacing: 2px;
        padding: 10px 0;
    }}

    /* Custom Tags */
    .tag-priority-high {{ color: #f85149; font-weight: bold; }}
    .tag-priority-medium {{ color: #d29922; font-weight: bold; }}
    .tag-priority-low {{ color: #3fb950; font-weight: bold; }}

    /* Danger Zone */
    .danger-zone {{
        border: 1px solid #f8514933;
        background-color: #f851490d;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
    }}

    /* Toggle Animations Off */
    {animation_css}
    </style>"""
    sm.markdown(dynamic_css, unsafe_allow_html=True)

# Inject CSS based on active preferences
inject_dynamic_css()

# --- 2. SYSTEM EMAIL CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "ai.study.companion.system@gmail.com"
SENDER_PASSWORD = "jzabfcdngkyhytla"

# --- 3. DATABASE ARCHITECTURE & MIGRATION ---
DB_FILE = "study_companion.db"
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Users Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                profile_pic TEXT, department TEXT DEFAULT '',
                course TEXT DEFAULT '',college TEXT DEFAULT '',
                current_semester TEXT DEFAULT '',
                study_goal TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)     
        # Ensure schema migrations for missing columns in existing user tables
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        for col_name in ['department', 'course', 'college', 'current_semester', 'study_goal']:
            if col_name not in columns:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} TEXT DEFAULT ''")
        # Tasks Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                task_name TEXT NOT NULL,
                due_date TEXT NOT NULL,
                priority TEXT DEFAULT 'Medium',
                category TEXT DEFAULT 'Personal',
                estimated_mins INTEGER DEFAULT 30,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY(username) REFERENCES users(username)
            )
        """)    
        cursor.execute("PRAGMA table_info(tasks)")
        task_cols = [col[1] for col in cursor.fetchall()]
        if 'priority' not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium'")
        if 'category' not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'Personal'")
        if 'estimated_mins' not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN estimated_mins INTEGER DEFAULT 30")

        # Deep Work History Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deep_work_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                task_name TEXT,
                duration_mins INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        """)

        # --- NEW: STUDY PLANNER DATABASE TABLE ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_planner (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                plan_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                study_topic TEXT NOT NULL,
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY(username) REFERENCES users(username)
            )
        """)

        conn.commit()

init_db()

# --- 4. CRYPTOGRAPHY & UTILITIES ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None

def send_otp_email(target_email, otp, context="Registration"):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"AI Study Companion <{SENDER_EMAIL}>"
        msg['To'] = target_email
        msg['Subject'] = f"[{context}] Verification Token"
        
        body = f"Hello,\n\nYour Verification OTP Token is: {otp}\n\nThis token is valid for your current session."
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, target_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        sm.sidebar.error(f"Mail Transmission Fault: {e}")
        return False

# --- 5. SESSION STATE MANAGEMENT ---
if "authenticated" not in sm.session_state:
    sm.session_state.authenticated = False
if "user" not in sm.session_state:
    sm.session_state.user = None
if "otp_stored" not in sm.session_state:
    sm.session_state.otp_stored = None
if "reg_data" not in sm.session_state:
    sm.session_state.reg_data = {}

# Timer Session States
if "timer_running" not in sm.session_state:
    sm.session_state.timer_running = False
if "timer_paused" not in sm.session_state:
    sm.session_state.timer_paused = False
if "timer_seconds_remaining" not in sm.session_state:
    sm.session_state.timer_seconds_remaining = 30 * 60
if "timer_total_duration" not in sm.session_state:
    sm.session_state.timer_total_duration = 30 * 60
if "timer_last_update" not in sm.session_state:
    sm.session_state.timer_last_update = None
if "timer_task_name" not in sm.session_state:
    sm.session_state.timer_task_name = "General Deep Work"

# --- 6. AUTHENTICATION MODULE ---
def auth_view():
    st_col1, st_col2, st_col3 = sm.columns([1, 2, 1])
    with st_col2:
        sm.title("🧠 AI Study Companion")
        sm.caption("High-Performance Academic & Focus Operating System")
        
        tabs = sm.tabs(["🔒 Login", "📝 Create Account", "🔑 Account Recovery"])
        
        # --- LOGIN ---
        with tabs[0]:
            sm.subheader("Account Login")
            login_user = sm.text_input("Username", key="login_uid").strip()
            login_pass = sm.text_input("Password", type="password", key="login_pwd")
     
            if sm.button("Authenticate Session", type="primary", use_container_width=True):
                if login_user and login_pass:
                    hashed = hash_password(login_pass)
                    normalized_login_user = login_user.lower()
                    
                    with get_db_connection() as conn:
                        user = conn.execute(
                            "SELECT * FROM users WHERE LOWER(username) = ? AND password_hash = ?", 
                            (normalized_login_user, hashed)
                        ).fetchone()
                    if user:
                        sm.session_state.authenticated = True
                        sm.session_state.user = dict(user)
                        sm.success(f"Access Granted. Welcome back, {user['username']}!")
                        time.sleep(0.8)
                        sm.rerun()
                    else:
                        sm.error("Invalid security credentials provided.")
                else:
                    sm.warning("Please fill out all identification fields.")
        # --- REGISTRATION ---
        with tabs[1]:
            sm.subheader("Register Verified Account")
            if sm.session_state.otp_stored is None:
                reg_user = sm.text_input("Username", key="reg_uid").strip()
                reg_email = sm.text_input("Student Email Address", key="reg_mail").strip()
                reg_pass = sm.text_input("Password", type="password", key="reg_pwd")
                reg_conf = sm.text_input("Confirm Password", type="password", key="reg_cpwd")
                
                if sm.button("Send Verification Token", use_container_width=True):
                    if not reg_user or not reg_email or not reg_pass:
                        sm.error("All registration fields are mandatory.")
                    elif reg_pass != reg_conf:
                        sm.error("Passwords do not match.")
                    elif not is_valid_email(reg_email):
                        sm.error("Invalid email address syntax.")
                    else:
                        normalized_reg_user = reg_user.lower()
                        with get_db_connection() as conn:
                            existing = conn.execute(
                                "SELECT username FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?", 
                                (normalized_reg_user, reg_email.lower())
                            ).fetchone()
                        if existing:
                            sm.error("Username or email is already registered.")
                        else:
                            generated_otp = str(random.randint(100000, 999999))
                            if send_otp_email(reg_email, generated_otp, "Registration"):
                                sm.session_state.otp_stored = generated_otp
                                sm.session_state.reg_data = {
                                    "username": normalized_reg_user, 
                                    "email": reg_email.lower(), 
                                    "password": reg_pass
                                }
                                sm.success("Verification token sent! Check your email inbox.")
                                sm.rerun()
            else:
                sm.info(f"Verification token sent to {sm.session_state.reg_data['email']}")
                entered_otp = sm.text_input("Enter 6-Digit OTP Token", key="reg_otp").strip()
                
                c1, c2 = sm.columns(2)
                with c1:
                    if sm.button("Verify & Complete Setup", type="primary", use_container_width=True):
                        if entered_otp == sm.session_state.otp_stored:
                            data = sm.session_state.reg_data
                            hashed = hash_password(data['password'])
                            
                            with get_db_connection() as conn:
                                conn.execute(
                                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                                    (data['username'], data['email'], hashed)
                                )
                                conn.commit()
                            sm.success("Account provisioned successfully! Proceed to login.")
                            sm.session_state.otp_stored = None
                            sm.session_state.reg_data = {}
                            time.sleep(1.2)
                            sm.rerun()
                        else:
                            sm.error("Token mismatch or expired.")
                with c2:
                    if sm.button("Cancel Registration", use_container_width=True):
                        sm.session_state.otp_stored = None
                        sm.session_state.reg_data = {}
                        sm.rerun()
        # --- RECOVERY ---
        with tabs[2]:
            sm.subheader("Account Password Recovery")
            if "recovery_otp" not in sm.session_state:
                rec_email = sm.text_input("Registered Email Address", key="rec_mail").strip()
                if sm.button("Request Recovery Token", use_container_width=True):
                    normalized_rec_email = rec_email.lower()
                    with get_db_connection() as conn:
                        user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (normalized_rec_email,)).fetchone()
                    if user:
                        gen_otp = str(random.randint(100000, 999999))
                        if send_otp_email(rec_email, gen_otp, "Account Recovery"):
                            sm.session_state.recovery_otp = gen_otp
                            sm.session_state.recovery_email = normalized_rec_email
                            sm.success("Recovery token transmitted to email.")
                            sm.rerun()
                    else:
                        sm.error("No account found matching that email address.")
            else:
                sm.info(f"Token dispatched to {sm.session_state.recovery_email}")
                entered_rec_otp = sm.text_input("Recovery Token", key="rec_otp_val").strip()
                text_pwd = sm.text_input("New Secure Password", type="password", key="rec_new_pwd")
                if sm.button("Reset Password", type="primary", use_container_width=True):
                    if entered_rec_otp == sm.session_state.recovery_otp:
                        if len(text_pwd) >= 4:
                            hashed = hash_password(text_pwd)
                            with get_db_connection() as conn:
                                conn.execute("UPDATE users SET password_hash = ? WHERE LOWER(email) = ?", 
                                             (hashed, sm.session_state.recovery_email))
                                conn.commit()
                            sm.success("Password reset successfully! Log in with new password.")
                            del sm.session_state.recovery_otp
                            del sm.session_state.recovery_email
                            time.sleep(1.2)
                            sm.rerun()
                        else:
                            sm.error("Password string too short.")
                    else:
                        sm.error("Invalid token.")

# --- 7. MAIN DASHBOARD PANELS ---
def render_dashboard(user):
    sm.title("🎯 Core Performance Center")
    sm.caption("Real-time Overview & Productivity Status")
    # Fetch User Stats from Database
    with get_db_connection() as conn:
        tasks = conn.execute("SELECT * FROM tasks WHERE username = ?", (user['username'],)).fetchall()
        sessions = conn.execute("SELECT * FROM deep_work_sessions WHERE username = ?", (user['username'],)).fetchall()
    completed_tasks = [t for t in tasks if t['status'] == 'Completed']
    total_minutes = sum([s['duration_mins'] for s in sessions])
    total_hours = round(total_minutes / 60.0, 1)
    # Top KPI Metrics Row
    k1, k2, k3, k4 = sm.columns(4)
    with k1:
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Total Study Time</div>
            <div class="kpi-value">{total_hours} hrs</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Focus Sessions</div>
            <div class="kpi-value">{len(sessions)}</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Tasks Completed</div>
            <div class="kpi-value">{len(completed_tasks)} / {len(tasks)}</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        score = min(100, int((len(completed_tasks)*10) + (len(sessions)*15)))
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Productivity Score</div>
            <div class="kpi-value">{score} pts</div>
        </div>
        """, unsafe_allow_html=True)
    c1, c2 = sm.columns([2, 1])
    with c1:
        sm.subheader("📌 Today's Priority Target")
        pending_high = [t for t in tasks if t['status'] == 'Pending' and t['priority'] in ['High', 'Critical']]
        if pending_high:
            top_task = pending_high[0]
            sm.info(f"**Target:** {top_task['task_name']} | **Category:** {top_task['category']} | **Priority:** {top_task['priority']} | **Due:** {top_task['due_date']}")
            if sm.button("🚀 Quick Launch Deep Work Session for this Task", type="primary"):
                sm.session_state.timer_task_name = top_task['task_name']
                sm.session_state.active_nav = "Deep Work"
                sm.rerun()
        else:
            sm.success("✨ Zero high-priority targets pending. Excellent work!")
    with c2:
        sm.subheader("💡 Performance Insight")
        if len(sessions) > 5:
            sm.write("🔥 **Strong momentum!** Your consistency is building solid deep-work retention.")
        else:
            sm.write("🌱 **Building habits:** Complete a 30+ minute Focus session to increase your productivity score.")

def render_deep_work(user):
    sm.title("🧠 Deep Work Environment")
    sm.caption("Strict 30+ Minute Structured Focus Execution")
    # Persistent Time Engine Logic
    now = time.time()
    if sm.session_state.timer_running and not sm.session_state.timer_paused:
        if sm.session_state.timer_last_update is not None:
            delta = now - sm.session_state.timer_last_update
            sm.session_state.timer_seconds_remaining -= delta
        sm.session_state.timer_last_update = now

        if sm.session_state.timer_seconds_remaining <= 0:
            sm.session_state.timer_running = False
            sm.session_state.timer_seconds_remaining = 0
            
            # Record Session in DB
            completed_mins = int(sm.session_state.timer_total_duration / 60)
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO deep_work_sessions (username, task_name, duration_mins) VALUES (?, ?, ?)",
                    (user['username'], sm.session_state.timer_task_name, completed_mins)
                )
                conn.commit()
            sm.balloons()
            sm.success("🎉 Deep Work Cycle Completed successfully! Progress recorded.")

    # Timer Setup Controls
    if not sm.session_state.timer_running and sm.session_state.timer_seconds_remaining == sm.session_state.timer_total_duration:
        sm.subheader("⚙️ Session Configuration")
        col_t1, col_t2 = sm.columns(2)
        
        with col_t1:
            sm.session_state.timer_task_name = sm.text_input("Active Target Task Name", value=sm.session_state.timer_task_name)
            preset = sm.selectbox("Duration Preset", ["30 Minutes", "45 Minutes", "60 Minutes", "90 Minutes", "120 Minutes", "Custom Duration"])

        with col_t2:
            if preset == "Custom Duration":
                h_col, m_col, s_col = sm.columns(3)
                with h_col:
                    custom_hrs = sm.number_input("Hours", min_value=0, max_value=24, value=0, step=1)
                with m_col:
                    custom_mins = sm.number_input("Minutes", min_value=0, max_value=59, value=30, step=1)
                with s_col:
                    custom_secs = sm.number_input("Seconds", min_value=0, max_value=59, value=0, step=1)
                
                total_duration_sec = (custom_hrs * 3600) + (custom_mins * 60) + custom_secs
            else:
                custom_mins = int(preset.split()[0])
                total_duration_sec = custom_mins * 60

        sm.warning("⚠️ **System Rule:** Deep Work sessions must be at least 30 minutes in length.")

        if sm.button("Initialize Focus Session", type="primary"):
            if total_duration_sec < 1800:
                sm.error("❌ Session rejected: Focus duration cannot be less than 30 minutes.")
            else:
                sm.session_state.timer_total_duration = total_duration_sec
                sm.session_state.timer_seconds_remaining = total_duration_sec
                sm.session_state.timer_running = True
                sm.session_state.timer_paused = False
                sm.session_state.timer_last_update = time.time()
                sm.rerun()

    # Active Timer Display Panel
    else:
        rem_sec = max(0, int(sm.session_state.timer_seconds_remaining))
        mins, secs = divmod(rem_sec, 60)
        hours, mins = divmod(mins, 60)

        time_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
        
        sm.markdown(f"### Current Task: **{sm.session_state.timer_task_name}**")
        sm.markdown(f"<div class='timer-display'>{time_str}</div>", unsafe_allow_html=True)
        
        progress = 1.0 - (sm.session_state.timer_seconds_remaining / sm.session_state.timer_total_duration)
        sm.progress(min(1.0, max(0.0, progress)))

        # Control Buttons
        c1, c2, c3, c4 = sm.columns(4)
        with c1:
            if sm.session_state.timer_running and not sm.session_state.timer_paused:
                if sm.button("⏸️ Pause Session", use_container_width=True):
                    sm.session_state.timer_paused = True
                    sm.rerun()
            elif sm.session_state.timer_paused:
                if sm.button("▶️ Resume Session", type="primary", use_container_width=True):
                    sm.session_state.timer_paused = False
                    sm.session_state.timer_last_update = time.time()
                    sm.rerun()

        with c2:
            if sm.button("🔄 Reset Timer", use_container_width=True):
                sm.session_state.timer_running = False
                sm.session_state.timer_paused = False
                sm.session_state.timer_seconds_remaining = sm.session_state.timer_total_duration
                sm.rerun()

        with c3:
            if sm.button("🏁 Complete Session Early", use_container_width=True):
                completed_mins = int((sm.session_state.timer_total_duration - sm.session_state.timer_seconds_remaining) / 60)
                if completed_mins >= 30:
                    with get_db_connection() as conn:
                        conn.execute(
                            "INSERT INTO deep_work_sessions (username, task_name, duration_mins) VALUES (?, ?, ?)",
                            (user['username'], sm.session_state.timer_task_name, completed_mins)
                        )
                        conn.commit()
                    sm.success(f"Session saved with {completed_mins} minutes completed.")
                else:
                    sm.warning("Session completed early, but duration was under 30 mins so it was not logged.")
                
                sm.session_state.timer_running = False
                sm.session_state.timer_seconds_remaining = sm.session_state.timer_total_duration
                sm.rerun()

    # Session History Table
    sm.write("---")
    sm.subheader("📜 Recent Focus History")
    with get_db_connection() as conn:
        history = conn.execute(
            "SELECT task_name, duration_mins, completed_at FROM deep_work_sessions WHERE username = ? ORDER BY id DESC LIMIT 5",
            (user['username'],)
        ).fetchall()
    
    if history:
        sm.dataframe([dict(row) for row in history], use_container_width=True)
    else:
        sm.caption("No completed focus sessions logged yet.")

    # Trigger automatic reruns while the timer is actively counting down
    if sm.session_state.timer_running and not sm.session_state.timer_paused:
        time.sleep(1)
        sm.rerun()

def render_tasks(user):
    sm.title("⚡ Task Management Protocol")

    # New Task Form
    with sm.expander("➕ Add New Task Target", expanded=False):
        with sm.form("task_form"):
            t_name = sm.text_input("Task Description")
            c1, c2, c3 = sm.columns(3)
            with c1:
                t_due = sm.date_input("Due Date", min_value=date.today())
            with c2:
                t_priority = sm.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            with c3:
                t_category = sm.selectbox("Category", ["College", "Coding", "Project", "Assignment", "Personal", "Other"])
            
            submit_task = sm.form_submit_button("Commit Task", type="primary")
            if submit_task and t_name:
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO tasks (username, task_name, due_date, priority, category) VALUES (?, ?, ?, ?, ?)",
                        (user['username'], t_name, str(t_due), t_priority, t_category)
                    )
                    conn.commit()
                sm.success("Task committed to database.")
                sm.rerun()

    # Filters and List Display
    f_col1, f_col2 = sm.columns([1, 1])
    with f_col1:
        status_filter = sm.selectbox("Status Filter", ["All", "Pending", "Completed"])
    with f_col2:
        priority_filter = sm.selectbox("Priority Filter", ["All", "Low", "Medium", "High", "Critical"])

    with get_db_connection() as conn:
        query = "SELECT * FROM tasks WHERE username = ?"
        params = [user['username']]
        if status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)
        if priority_filter != "All":
            query += " AND priority = ?"
            params.append(priority_filter)
        
        all_tasks = conn.execute(query, params).fetchall()

    sm.write("---")
    if not all_tasks:
        sm.info("No matching task entries found.")
    else:
        for task in all_tasks:
            status_symbol = "✅" if task['status'] == 'Completed' else "⏳"
            col_a, col_b, col_c, col_d = sm.columns([3, 1, 1, 1])
            
            col_a.write(f"**{status_symbol} {task['task_name']}** (`{task['category']}`)")
            col_b.write(f"Due: `{task['due_date']}`")
            col_c.write(f"Priority: **{task['priority']}**")
           
            if task['status'] == 'Pending':
                if col_d.button("Done", key=f"done_{task['id']}"):
                    with get_db_connection() as conn:
                        conn.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (task['id'],))
                        conn.commit()
                    sm.rerun()
            else:
                if col_d.button("Delete", key=f"del_{task['id']}"):
                    with get_db_connection() as conn:
                        conn.execute("DELETE FROM tasks WHERE id = ?", (task['id'],))
                        conn.commit()
                    sm.rerun()

# --- NEW: STUDY PLANNER MODULE ---
def render_planner(user):
    sm.title("📅 Daily Study Planner")
    sm.caption("Schedule and track chronological study blocks for optimal time blocking.")

    # 1. Date Selection Header & Control Row
    col_d1, col_d2 = sm.columns([1, 2])
    with col_d1:
        selected_date = sm.date_input("Select Planning Date", value=date.today())
    
    selected_date_str = str(selected_date)

    # 2. Add New Study Block Expander
    with sm.expander("➕ Add Planned Study Block", expanded=False):
        with sm.form("planner_form"):
            p_topic = sm.text_input("Study Topic / Task Name")
            col_t1, col_t2 = sm.columns(2)
            with col_t1:
                p_start = sm.time_input("Start Time", value=dtime(9, 0))
            with col_t2:
                p_end = sm.time_input("End Time", value=dtime(10, 0))
            
            p_notes = sm.text_area("Optional Notes / Material Links", value="")

            submit_plan = sm.form_submit_button("Save Study Block", type="primary")

            if submit_plan:
                if not p_topic:
                    sm.error("Please enter a study topic.")
                elif p_start >= p_end:
                    sm.error("Start Time must be strictly earlier than End Time.")
                else:
                    with get_db_connection() as conn:
                        conn.execute("""
                            INSERT INTO study_planner (username, plan_date, start_time, end_time, study_topic, notes, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
                        """, (user['username'], selected_date_str, str(p_start), str(p_end), p_topic, p_notes))
                        conn.commit()
                    sm.success("Study block successfully scheduled!")
                    time.sleep(0.5)
                    sm.rerun()

    # 3. Retrieve Blocks for Selected Date
    with get_db_connection() as conn:
        blocks = conn.execute("""
            SELECT * FROM study_planner 
            WHERE username = ? AND plan_date = ?
            ORDER BY start_time ASC
        """, (user['username'], selected_date_str)).fetchall()

    # Calculate Daily Summary Statistics
    total_blocks = len(blocks)
    completed_blocks = len([b for b in blocks if b['status'] == 'Completed'])
    
    total_planned_minutes = 0
    for b in blocks:
        try:
            t1 = datetime.strptime(b['start_time'], "%H:%M:%S")
            t2 = datetime.strptime(b['end_time'], "%H:%M:%S")
        except ValueError:
            t1 = datetime.strptime(b['start_time'], "%H:%M")
            t2 = datetime.strptime(b['end_time'], "%H:%M")
        
        diff = (t2 - t1).total_seconds() / 60
        if diff > 0:
            total_planned_minutes += diff

    total_planned_hours = round(total_planned_minutes / 60.0, 1)

    # Display KPI Cards for Planner
    sm.write("")
    pk1, pk2, pk3 = sm.columns(3)
    with pk1:
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Total Planned Time</div>
            <div class="kpi-value">{total_planned_hours} hrs</div>
        </div>
        """, unsafe_allow_html=True)
    with pk2:
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Total Blocks</div>
            <div class="kpi-value">{total_blocks}</div>
        </div>
        """, unsafe_allow_html=True)
    with pk3:
        sm.markdown(f"""
        <div class="saas-card">
            <div class="kpi-title">Blocks Completed</div>
            <div class="kpi-value">{completed_blocks} / {total_blocks}</div>
        </div>
        """, unsafe_allow_html=True)

    sm.write("---")
    sm.subheader(f"📖 Schedule for {selected_date.strftime('%B %d, %Y')}")

    if not blocks:
        sm.info(f"No study blocks planned for {selected_date_str}. Use the form above to add blocks.")
    else:
        for block in blocks:
            status_flag = "✅" if block['status'] == 'Completed' else "⏳"
            start_formatted = block['start_time'][:5]
            end_formatted = block['end_time'][:5]

            c_time, c_info, c_actions = sm.columns([1.5, 3.5, 1])
            
            with c_time:
                sm.markdown(f"⏱️ **{start_formatted} - {end_formatted}**")

            with c_info:
                if block['status'] == 'Completed':
                    sm.markdown(f"~**{block['study_topic']}**~ {status_flag}")
                else:
                    sm.markdown(f"**{block['study_topic']}** {status_flag}")
                
                if block['notes']:
                    sm.caption(f"📝 {block['notes']}")

            with c_actions:
                act_col1, act_col2 = sm.columns(2)
                if block['status'] == 'Pending':
                    if act_col1.button("✔", key=f"plan_done_{block['id']}", help="Mark as Completed"):
                        with get_db_connection() as conn:
                            conn.execute("UPDATE study_planner SET status = 'Completed' WHERE id = ?", (block['id'],))
                            conn.commit()
                        sm.rerun()
                
                if act_col2.button("🗑️", key=f"plan_del_{block['id']}", help="Delete Study Block"):
                    with get_db_connection() as conn:
                        conn.execute("DELETE FROM study_planner WHERE id = ?", (block['id'],))
                        conn.commit()
                    sm.rerun()

def render_analytics(user):
    sm.title("📊 Performance & Study Analytics")
    with get_db_connection() as conn:
        sessions = conn.execute("SELECT * FROM deep_work_sessions WHERE username = ?", (user['username'],)).fetchall()
        tasks = conn.execute("SELECT * FROM tasks WHERE username = ?", (user['username'],)).fetchall()
    if not sessions and not tasks:
        sm.info("Insufficient activity data to render visual analytics.")
        return
    # Task Completion Pie Chart
    a1, a2 = sm.columns(2)
    with a1:
        sm.subheader("Task Completion Status")
        completed = len([t for t in tasks if t['status'] == 'Completed'])
        pending = len([t for t in tasks if t['status'] == 'Pending'])     
        if tasks:
            fig_pie = px.pie(
                values=[completed, pending], 
                names=['Completed', 'Pending'],
                color_discrete_sequence=['#2ea043', '#f85149'],
                hole=0.4
            )
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#c9d1d9')
            sm.plotly_chart(fig_pie, use_container_width=True)
    with a2:
        sm.subheader("Focus Duration Trends")
        if sessions:
            df_sessions = [dict(s) for s in sessions]
            fig_bar = px.bar(
                df_sessions, 
                x='completed_at', 
                y='duration_mins', 
                title="Deep Work Minutes Per Session",
                color_discrete_sequence=['#58a6ff']
            )
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#c9d1d9')
            sm.plotly_chart(fig_bar, use_container_width=True)

def render_profile(user):
    sm.title("👤 Student Identity Profile")    
    with sm.form("profile_form"):
        col1, col2 = sm.columns(2)
        with col1:
            department = sm.text_input("Department/Major", value=user.get('department', ''))
            course = sm.text_input("Degree / Course", value=user.get('course', ''))
            college = sm.text_input("University / College", value=user.get('college', ''))
        with col2:
            current_semester = sm.text_input("Current Semester / Year",value=user.get('current_semester', ''))
            study_goal = sm.text_area("Primary Academic Goal",value=user.get('study_goal', ''))
            uploaded_file = sm.file_uploader("Upload New Profile Picture", type=["png", "jpg", "jpeg"])
        if sm.form_submit_button("Update Profile Data", type="primary"):
            encoded_pic = user['profile_pic']
            if uploaded_file is not None:
                bytes_data = uploaded_file.read()
                encoded_pic = base64.b64encode(bytes_data).decode('utf-8')
            with get_db_connection() as conn:
                conn.execute("""UPDATE users SET department = ?, course = ?, college = ?, current_semester = ?, study_goal = ?, profile_pic = ? WHERE username = ?""", 
                             (department, course, college, current_semester, study_goal, encoded_pic, user['username']))
                conn.commit()
            sm.session_state.user['department'] = department
            sm.session_state.user['course'] = course
            sm.session_state.user['college'] = college
            sm.session_state.user['current_semester'] = current_semester
            sm.session_state.user['study_goal'] = study_goal
            sm.session_state.user['profile_pic'] = encoded_pic          
            sm.success("Profile saved successfully!")
            sm.rerun()

# --- DYNAMICALLY INTEGRATED SETTINGS CONTROL CENTER ---
def render_settings():
    sm.title("⚙️ System Preferences & Control Center")
    sm.caption("Manage session rules, interface theme, notification triggers, and user account parameters.")
    sm.write("")

    prefs = sm.session_state.user_prefs
    user = sm.session_state.user

    # -------------------------------------------------------------
    # SECTION 1: STUDY & SESSION PARAMETERS
    # -------------------------------------------------------------
    with sm.expander("📚 Study Settings & Focus Rules", expanded=True):
        sm.markdown("Configure target durations, rest cycles, and daily targets.")
        
        c1, c2 = sm.columns(2)
        with c1:
            def_focus = sm.number_input(
                "Default Session Focus Duration (Mins)", 
                min_value=30, max_value=240, 
                value=int(prefs.get("default_focus", 30)), 
                step=5,
                help="System enforces a 30-minute minimum threshold for deep work."
            )
            short_b = sm.number_input(
                "Short Break Duration (Mins)", 
                min_value=1, max_value=30, 
                value=int(prefs.get("short_break", 5)), step=1
            )
            long_b = sm.number_input(
                "Long Break Duration (Mins)", 
                min_value=5, max_value=60, 
                value=int(prefs.get("long_break", 15)), step=5
            )

        with c2:
            daily_goal = sm.number_input(
                "Daily Target Study Goal (Hours)", 
                min_value=0.5, max_value=16.0, 
                value=float(prefs.get("daily_goal_hrs", 4.0)), step=0.5
            )
            remind_before = sm.toggle(
                "Enable Session Pre-Start Reminder", 
                value=prefs.get("remind_before", True)
            )
            remind_mins = sm.slider(
                "Reminder Lead Time (Minutes before session)", 
                min_value=1, max_value=30, 
                value=int(prefs.get("remind_mins", 10)),
                disabled=not remind_before
            )

    # -------------------------------------------------------------
    # SECTION 2: DYNAMIC APPEARANCE & USER INTERFACE
    # -------------------------------------------------------------
    with sm.expander("🎨 Appearance & Display Preferences", expanded=True):
        sm.markdown("Customize your visual workspace environment. Changes apply instantly upon saving.")
        
        theme_options = ["Midnight OLED / Eye Protect", "Dark SaaS", "Light Modern", "High Contrast Dark"]
        current_theme_idx = theme_options.index(prefs.get("theme", "Midnight OLED / Eye Protect")) if prefs.get("theme") in theme_options else 0
        
        col_ui1, col_ui2 = sm.columns(2)
        with col_ui1:
            theme = sm.selectbox(
                "Color Theme", 
                theme_options,
                index=current_theme_idx,
                help="'Midnight OLED / Eye Protect' uses low blue light tones designed for late-night focus."
            )
            font_size = sm.select_slider(
                "UI Font Scale", 
                options=["Small", "Medium", "Large"], 
                value=prefs.get("font_size", "Medium")
            )
        with col_ui2:
            layout_density = sm.radio(
                "Layout Density", 
                ["Comfortable", "Compact"], 
                horizontal=True,
                index=0 if prefs.get("layout_density", "Comfortable") == "Comfortable" else 1
            )
            animations = sm.toggle(
                "Enable Interface Animations & Transitions", 
                value=prefs.get("animations", True)
            )

    # -------------------------------------------------------------
    # SECTION 3: NOTIFICATION DISPATCHER
    # -------------------------------------------------------------
    with sm.expander("🔔 Notification & Alert Rules", expanded=False):
        sm.markdown("Control email triggers, deadline warnings, and audio chimes.")
        
        n1, n2 = sm.columns(2)
        with n1:
            notify_reminders = sm.toggle(
                "Upcoming Session Reminders", 
                value=prefs.get("notify_reminders", True)
            )
            notify_deadlines = sm.toggle(
                "Task Deadline Warnings (24 hrs prior)", 
                value=prefs.get("notify_deadlines", True)
            )
        with n2:
            notify_summary = sm.toggle(
                "Daily Study Summary Digest via Email", 
                value=prefs.get("notify_summary", False)
            )
            notify_sound = sm.toggle(
                "Play Completion Sound Chime", 
                value=prefs.get("notify_sound", True)
            )

    # -------------------------------------------------------------
    # SECTION 4: ACCOUNT CONTROLS & DATA PORTABILITY
    # -------------------------------------------------------------
    with sm.expander("👤 Account Controls & Data Portability", expanded=False):
        sm.markdown("Manage credentials, security, and personal data exports.")
        
        acc_tabs = sm.tabs(["📋 Identity Overview", "🔑 Change Password", "💾 Export Data", "🚪 Session Control", "🗑️ Delete Account"])
        
        # Identity Summary
        with acc_tabs[0]:
            col_prof1, col_prof2 = sm.columns([2, 1])
            with col_prof1:
                sm.write(f"**Username:** `{user['username']}`")
                sm.write(f"**Email:** `{user['email']}`")
                sm.write(f"**Department:** {user.get('department') or 'Not Set'}")
                sm.write(f"**University:** {user.get('college') or 'Not Set'}")
            with col_prof2:
                if sm.button("Edit Full Profile", use_container_width=True):
                    sm.session_state.active_nav = "Profile"
                    sm.rerun()

        # Change Password Form
        with acc_tabs[1]:
            with sm.form("change_pwd_form"):
                curr_pwd = sm.text_input("Current Password", type="password")
                new_pwd = sm.text_input("New Password", type="password")
                confirm_pwd = sm.text_input("Confirm New Password", type="password")
                
                if sm.form_submit_button("Update Password", type="primary"):
                    if not curr_pwd or not new_pwd or not confirm_pwd:
                        sm.error("All password fields are required.")
                    elif new_pwd != confirm_pwd:
                        sm.error("New passwords do not match.")
                    elif hash_password(curr_pwd) != user['password_hash']:
                        sm.error("Current password verification failed.")
                    elif len(new_pwd) < 4:
                        sm.error("New password must be at least 4 characters.")
                    else:
                        new_hash = hash_password(new_pwd)
                        with get_db_connection() as conn:
                            conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", 
                                         (new_hash, user['username']))
                            conn.commit()
                        sm.session_state.user['password_hash'] = new_hash
                        sm.success("Password updated successfully!")

        # Data Export (JSON)
        with acc_tabs[2]:
            sm.write("Export your study activity, tasks, and profile as a backup JSON file.")
            
            with get_db_connection() as conn:
                user_tasks = [dict(r) for r in conn.execute("SELECT * FROM tasks WHERE username = ?", (user['username'],)).fetchall()]
                user_sessions = [dict(r) for r in conn.execute("SELECT * FROM deep_work_sessions WHERE username = ?", (user['username'],)).fetchall()]
                user_planner = [dict(r) for r in conn.execute("SELECT * FROM study_planner WHERE username = ?", (user['username'],)).fetchall()]

            user_export_payload = {
                "user_profile": {
                    "username": user['username'],
                    "email": user['email'],
                    "department": user.get('department', ''),
                    "college": user.get('college', ''),
                    "created_at": user.get('created_at', '')
                },
                "tasks": user_tasks,
                "deep_work_history": user_sessions,
                "study_planner": user_planner,
                "exported_at": str(datetime.now())
            }
            
            json_string = json.dumps(user_export_payload, indent=4)
            
            sm.download_button(
                label="📄 Download Data Archive (JSON)",
                data=json_string,
                file_name=f"{user['username']}_study_data.json",
                mime="application/json",
                use_container_width=True
            )

        # Logout Action
        with acc_tabs[3]:
            sm.markdown("<div class='danger-zone'>", unsafe_allow_html=True)
            sm.write("**Session Control**")
            sm.caption("Logging out will clear active timer state and safely sign you out.")
            if sm.button("🚨 Terminate Session (Logout)", type="primary", use_container_width=True):
                sm.session_state.authenticated = False
                sm.session_state.user = None
                sm.rerun()
            sm.markdown("</div>", unsafe_allow_html=True)

        # --- NEW: DELETE ACCOUNT SECTION ---
        with acc_tabs[4]:
            sm.markdown("<div class='danger-zone'>", unsafe_allow_html=True)
            sm.error("⚠️ Permanent Account Deletion")
            sm.write("Deleting your account will **permanently remove** all your stored profile data, task entries, deep work sessions, and planner schedules from the system database. **This action cannot be undone.**")
            
            del_pwd = sm.text_input("Confirm Password", type="password", key="del_acc_pwd")
            del_confirm_str = sm.text_input("Type 'DELETE' to confirm", key="del_acc_str")

            if sm.button("🚨 Delete My Account Permanently", type="primary", use_container_width=True):
                if not del_pwd or not del_confirm_str:
                    sm.error("Please fill in both security confirmation fields.")
                elif del_confirm_str.strip() != "DELETE":
                    sm.error("Confirmation word mismatch. You must type exactly 'DELETE'.")
                elif hash_password(del_pwd) != user['password_hash']:
                    sm.error("Password verification failed. Incorrect password.")
                else:
                    # Proceed with full cascade deletion for this user only
                    with get_db_connection() as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (user['username'],))
                        conn.execute("DELETE FROM tasks WHERE username = ?", (user['username'],))
                        conn.execute("DELETE FROM deep_work_sessions WHERE username = ?", (user['username'],))
                        conn.execute("DELETE FROM study_planner WHERE username = ?", (user['username'],))
                        conn.commit()

                    # Reset session states
                    sm.session_state.authenticated = False
                    sm.session_state.user = None
                    sm.session_state.timer_running = False
                    sm.session_state.timer_paused = False
                    sm.session_state.active_nav = "Dashboard"

                    sm.success("Account permanently purged. Redirecting to authentication screen...")
                    time.sleep(1.5)
                    sm.rerun()

            sm.markdown("</div>", unsafe_allow_html=True)

    # Save Settings Button Action
    sm.write("")
    if sm.button("💾 Save All System Preferences", type="primary", use_container_width=True):
        sm.session_state.user_prefs = {
            "default_focus": def_focus,
            "short_break": short_b,
            "long_break": long_b,
            "daily_goal_hrs": daily_goal,
            "remind_before": remind_before,
            "remind_mins": remind_mins,
            "theme": theme,
            "font_size": font_size,
            "layout_density": layout_density,
            "animations": animations,
            "notify_reminders": notify_reminders,
            "notify_deadlines": notify_deadlines,
            "notify_summary": notify_summary,
            "notify_sound": notify_sound
        }
        sm.success("✅ System preferences updated and applied across application UI!")
        time.sleep(0.5)
        sm.rerun()

    # -------------------------------------------------------------
    # SECTION 5: ABOUT THE APPLICATION
    # -------------------------------------------------------------
    sm.write("---")
    with sm.expander("ℹ️ About AI Study Companion", expanded=False):
        a_col1, a_col2 = sm.columns([2, 1])
        with a_col1:
            sm.markdown("### 🧠 AI Study Companion")
            sm.markdown("**Version:** `2.5.0 (Dynamic Theme Production Release)`")
            sm.markdown("""
            **Purpose:** An intelligent academic workstation engineered to minimize distraction, 
            track structured deep-work focus sessions, manage high-priority targets, 
            and generate visual productivity analytics.
            
            **Key Features:**
            * ⏱️ Persistent 30+ minute timer with state preservation.
            * 🎨 Dynamic UI Theme & Font Scaler (Including Midnight OLED Eye Protection).
            * 🔐 OTP-verified registration and user authentication.
            * 📊 Interactive analytics dashboards powered by Plotly.
            """)
        with a_col2:
            sm.markdown("**Tech Stack Architecture:**")
            sm.markdown("- **Language:** Python 3.x")
            sm.markdown("- **Frontend:** Streamlit Engine")
            sm.markdown("- **Database:** SQLite3 / Relational Schema")
            sm.markdown("- **Visualization:** Plotly Express")
            sm.markdown("- **Auth:** SMTP + SHA-256 Hashing")
            
        sm.caption("🔒 **Privacy Notice:** Academic records and session logs are isolated per individual user account. Passwords are stored securely via cryptographic hashing.")

# --- 8. NAVIGATION ROUTER & SIDEBAR ---
def main_dashboard():
    user = sm.session_state.user
    # Sidebar Profile Card
    with sm.sidebar:
        sm.title("🧠 Core Suite")
        if user.get('profile_pic'):
            try:
                sm.image(base64.b64decode(user['profile_pic']), width=90)
            except Exception:
                sm.image("https://via.placeholder.com/90", width=90)
        else:
            sm.image("https://via.placeholder.com/90", width=90)
        sm.markdown(f"**{user['username']}**")
        sm.caption(user['email'])
        sm.write("---")
        # Dynamic State Navigation Selection
        if "active_nav" not in sm.session_state:
            sm.session_state.active_nav = "Dashboard"
        
        # Updated navigation menu with Planner
        nav_options = ["Dashboard", "Deep Work", "Tasks", "Planner", "Analytics", "Profile", "Settings"]
        
        if sm.session_state.active_nav not in nav_options:
            sm.session_state.active_nav = "Dashboard"

        nav_choice = sm.radio("Navigation", nav_options,
                              index=nav_options.index(sm.session_state.active_nav))
        sm.session_state.active_nav = nav_choice
        sm.write("---")
        if sm.button("Terminate Session (Logout)", use_container_width=True):
            sm.session_state.authenticated = False
            sm.session_state.user = None
            sm.rerun()

    # Route Selection
    if nav_choice == "Dashboard":
        render_dashboard(user)
    elif nav_choice == "Deep Work":
        render_deep_work(user)
    elif nav_choice == "Tasks":
        render_tasks(user)
    elif nav_choice == "Planner":
        render_planner(user)
    elif nav_choice == "Analytics":
        render_analytics(user)
    elif nav_choice == "Profile":
        render_profile(user)
    elif nav_choice == "Settings":
        render_settings()

# --- 9. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    if sm.session_state.authenticated:
        main_dashboard()
    else:
        auth_view()