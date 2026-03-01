import streamlit as st
import os
import pandas as pd
from models.recommendation import generate_recommendation
from models.feedback_model import train_model, predict_level
from resources.video_library import VIDEO_LIBRARY
from resources.resource_library import RESOURCE_LIBRARY
# 🔥 DATABASE IMPORTS
from database import create_tables, get_connection
import sqlite3

# SUBJECT-WISE QUIZ LINKS
QUIZ_LINKS = {
    "Mathematics": "https://forms.gle/5yStSdTRQBngVH998",
    "Physics": "https://forms.gle/zer4rhYCdxMsqga39",
    "Chemistry": "https://forms.gle/sXyiGCNHptAJNW3S6",
    "Biology": "https://forms.gle/sn7w7KDDzBZUJYWM7",
    "Computer Science": "https://forms.gle/Uv6cR9DxMEChoUKM7"
}

st.set_page_config(page_title="AI Personalized Learning Platform", layout="wide", initial_sidebar_state="expanded")

# 🔥 CREATE DATABASE TABLES
create_tables()

st.markdown("""
<style>
.stApp { background-color: #FFFFFF; }
section[data-testid="stSidebar"] { background-color: #C084FC; padding-top: 20px; }
section[data-testid="stSidebar"] * { color: #0F0F0F !important; font-weight: 500; }
.recommendation-card { background-color: #F3E8FF; padding: 30px; border-radius: 15px; border-left: 6px solid #C084FC; box-shadow: 0px 4px 12px rgba(0,0,0,0.08); margin-bottom: 25px; }
.stButton>button { background-color: #C084FC; color: #0F0F0F; border-radius: 8px; height: 45px; font-weight: 600; border: none; }
.stButton>button:hover { background-color: #A855F7; color: white; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("AI Learning System")
menu = st.sidebar.radio("Navigation", ["Login", "Main Dashboard", "Analytics", "Admin Panel", "About"])
st.sidebar.markdown("---")
st.sidebar.write("AI-Powered Personalized Education")

# SESSION STATE
if "current_recommendation" not in st.session_state: st.session_state.current_recommendation = None
if "learning_style" not in st.session_state: st.session_state.learning_style = None
if "selected_subject" not in st.session_state: st.session_state.selected_subject = None
if "subject_levels" not in st.session_state:
    st.session_state.subject_levels = {
        "Mathematics": "intermediate", "Physics": "intermediate", "Chemistry": "intermediate",
        "Biology": "intermediate", "Computer Science": "intermediate"
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

# 🔥 LOGIN SYSTEM
if menu == "Login":
    st.title("🔐 Login / Register")
    conn = get_connection()
    c = conn.cursor()
    
    option = st.radio("Select Option", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if option == "Register":
        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          (username, password, "student"))
                conn.commit()
                st.success("✅ Account Created Successfully!")
                st.info("Now login with your credentials")
            except sqlite3.IntegrityError:
                st.error("❌ Username already exists")
            except Exception as e:
                st.error(f"Error: {e}")
    
    if option == "Login":
        if st.button("Login"):
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
            result = c.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = result[0]
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    conn.close()
    st.stop()

# PROTECTED PAGES
if not st.session_state.logged_in:
    st.warning("👋 Please login first")
    st.stop()

# MAIN DASHBOARD
elif menu == "Main Dashboard":
    st.title(f"🤖 AI-Powered Learning Platform - Welcome, {st.session_state.username}!")
    
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        with col1: 
            name = st.text_input("Student Name", value=st.session_state.username, disabled=True)
            class_level = st.selectbox("Select Class Level", ["Class 8", "Class 9", "Class 10", "Class 11", "Class 12"])
        with col2:
            subject = st.selectbox("Subject of Interest", ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"])
            learning_style = st.radio("Preferred Learning Style", ["Videos", "Reading", "Practice Problems"])
        performance = st.slider("Current Performance (%)", 0, 100, 50)
        goal = st.text_area("Describe Your Learning Goal")
        submitted = st.form_submit_button("Generate Recommendation")

    if submitted:
        profile = {"name": st.session_state.username, "class_level": class_level, "subject": subject, 
                  "learning_style": learning_style, "performance": performance, "intent": "General Learning", "content_type": "video"}
        recommendations = generate_recommendation(profile)
        st.session_state.current_recommendation = recommendations[0]
        st.session_state.learning_style = learning_style
        st.session_state.selected_subject = subject

    if st.session_state.current_recommendation:
        rec = st.session_state.current_recommendation
        subject = st.session_state.selected_subject
        level = st.session_state.subject_levels.get(subject, "intermediate")
        
        st.markdown("## 📚 Recommended Learning Plan")
        quizzes_count = rec.get('quizzes', rec.get('videos', 0) // 2)
        
        st.markdown(f"""
        <div class="recommendation-card">
        <h3>{rec['course']}</h3>
        <p><strong>🤖 AI Level:</strong> <span style="color:#C084FC">{level.title()}</span></p>
        <p><strong>Difficulty:</strong> {rec['difficulty']}</p>
        <p><strong>Duration:</strong> {rec['duration']}</p>
        <p><strong>Priority:</strong> {rec['priority']}</p>
        <p><strong>📹 Videos:</strong> {rec['videos']} | <strong>📝 Quizzes:</strong> {quizzes_count}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🎥 Learning Materials")
        
        if st.session_state.learning_style == "Videos":
            videos = VIDEO_LIBRARY.get(subject, {}).get(level, [])
            if videos:
                for video in videos: 
                    st.video(video)
            else:
                st.info(f"No videos available for {subject} {level} level.")

        elif st.session_state.learning_style == "Reading":
            resources = RESOURCE_LIBRARY.get(subject, {}).get("Reading", [])
            if resources:
                for resource in resources:
                    file_path = resource["file"]
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(label=f"📖 {resource['title']}", data=f, 
                                            file_name=os.path.basename(file_path), mime="application/pdf")
                    else:
                        st.warning(f"File not found: {resource['title']}")
            else:
                st.info("No reading resources available.")

        elif st.session_state.learning_style == "Practice Problems":
            st.markdown("### 🧮 Practice Questions")
            st.write("1. Solve 10 topic-based questions")
            st.write("2. Attempt previous year board questions") 
            st.write("3. Complete 1 timed mock test")
            st.write("4. Review mistakes and retry incorrect ones")
            st.success("Practice module activated!")

        # QUIZ & ACHIEVEMENTS
        st.markdown("### 📊 Take Quiz")
        quiz_link = QUIZ_LINKS.get(subject)
        if quiz_link:
            st.link_button(f"Start {subject} Quiz", quiz_link)
        else:
            st.warning("Quiz not available for this subject yet.")
        
        st.markdown("### 🎯 Enter Quiz Score")
        score = st.number_input("Score (out of 10)", 0, 10, 5)
        progress = score * 10
        st.progress(progress)
        st.success(f"Progress: {progress}%")

        if score >= 8: 
            st.success("🥇 Gold Badge! 🎉")
            st.balloons()
        elif score >= 5: 
            st.info("🥈 Silver Badge!")
        else: 
            st.warning("🥉 Keep Practicing!")

        # 🔥 PREVIOUS ATTEMPTS (MOVED HERE - FIXED INDENTATION)
        st.markdown("### 📜 Previous Attempts")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        SELECT subject, level, rating, quiz_score, timestamp
        FROM session_logs
        WHERE username=?
        ORDER BY timestamp DESC
        LIMIT 10
        """, (st.session_state.username,))
        rows = c.fetchall()
        conn.close()

        if rows:
            df_history = pd.DataFrame(rows, columns=["Subject", "Level", "Rating", "Quiz Score", "Time"])
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("📝 No previous attempts yet. Complete your first session!")

        # 🔥 ML FEEDBACK SECTION
        st.markdown("---")
        st.subheader("🤖 AI Adaptive Learning")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            feedback_rating = st.slider("Rate this content (1=Poor, 5=Excellent)", 1, 5, 3)
        with col2:
            st.metric("AI Level", level.title())

        if st.button("🚀 Train AI & Update Level", type="primary"):
            # 🔥 SAVE TO DATABASE (NO CSV)
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
            INSERT INTO session_logs (username, subject, level, rating, quiz_score)
            VALUES (?, ?, ?, ?, ?)
            """, (st.session_state.username, subject, level, feedback_rating, score))
            conn.commit()
            conn.close()

            # RETRAIN MODEL
            st.info("🔄 Training AI model...")
            train_model()

            # AI PREDICTION
            predicted_level = predict_level("General Learning", subject, "video", feedback_rating, score)
            
            if predicted_level:
                old_level = st.session_state.subject_levels[subject]
                st.session_state.subject_levels[subject] = predicted_level
                st.success(f"🤖 AI upgraded from **{old_level.title()}** → **{predicted_level.title()}**!")
                st.balloons()
            else:
                st.warning("ℹ️ Need more data for AI predictions (collect 5+ ratings)")
            
            st.rerun()

        st.caption(f"**AI Status:** {subject}: {level.title()} ({len(VIDEO_LIBRARY.get(subject, {}).get(level, []))} videos)")

# ANALYTICS
elif menu == "Analytics":
    st.title("📈 Learning Analytics")
    st.info("Analytics coming soon with ML insights!")

# ADMIN PANEL
elif menu == "Admin Panel":
    st.title("⚙️ Admin Panel")
    if st.session_state.role != "admin":
        st.error("❌ Access Denied - Admin only")
        st.stop()
    else:
        conn = get_connection()
        df_users = pd.read_sql("SELECT id, username, role FROM users", conn)
        df_logs = pd.read_sql("SELECT * FROM session_logs ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👥 Registered Users")
            st.dataframe(df_users, use_container_width=True)
        with col2:
            st.subheader("📊 Recent Activity")
            st.dataframe(df_logs, use_container_width=True)

        st.subheader("📈 Engagement Metrics")
        st.metric("Total Users", len(df_users))
        st.metric("Total Sessions", len(df_logs))

# ABOUT
elif menu == "About":
    st.title("ℹ️ About")
    st.markdown("""
    **🤖 ML-Powered Adaptive Learning:**
    - **Rule-based** initial recommendations
    - **ML LogisticRegression** adapts levels from feedback
    - **Per-subject memory** - Mathematics ≠ Physics levels
    - **Continuous learning** - model retrains automatically
    - **Persistent storage** - SQLite database
    - **Multi-user ready** - Login system + Admin panel
    """)
