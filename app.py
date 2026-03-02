import streamlit as st
import os
import pandas as pd
from models.recommendation import generate_recommendation
from models.feedback_model import train_model, predict_level
from resources.video_library import VIDEO_LIBRARY
from resources.resource_library import RESOURCE_LIBRARY
from database import create_tables, get_connection
import sqlite3

QUIZ_LINKS = {
    "Mathematics": "https://forms.gle/5yStSdTRQBngVH998",
    "Physics": "https://forms.gle/zer4rhYCdxMsqga39",
    "Chemistry": "https://forms.gle/sXyiGCNHptAJNW3S6",
    "Biology": "https://forms.gle/sn7w7KDDzBZUJYWM7",
    "Computer Science": "https://forms.gle/Uv6cR9DxMEChoUKM7"
}

st.set_page_config(page_title="AI Personalized Learning Platform", layout="wide", initial_sidebar_state="expanded")

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
if "menu" not in st.session_state: st.session_state.menu = "Login"

create_tables()

st.markdown("""
<style>
.stApp { background-color: #FFFFFF; }
section[data-testid="stSidebar"] { background-color: #C084FC; padding-top: 20px; }
section[data-testid="stSidebar"] * { color: #0F0F0F !important; font-weight: 500; }
.recommendation-card, .admin-card { background-color: #F3E8FF; padding: 20px; border-radius: 15px; border-left: 6px solid #C084FC; margin-bottom: 20px; }
.stButton>button { background-color: #C084FC; color: #0F0F0F; border-radius: 8px; height: 45px; font-weight: 600; }
.stButton>button:hover { background-color: #A855F7; color: white; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("AI Learning System")

if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as: {st.session_state.username} ({st.session_state.role})")

    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.menu = "Login"
        st.rerun()

    st.sidebar.markdown("---")
    
    if st.session_state.role == "admin":
        st.session_state.menu = st.sidebar.radio(
            "Navigation",
            ["Admin Panel", "Analytics", "About"]
        )
    else:
        st.session_state.menu = st.sidebar.radio(
            "Navigation",
            ["Main Dashboard", "Analytics", "About"]
        )
else:
    st.session_state.menu = "Login"

menu = st.session_state.menu
st.sidebar.markdown("---")
st.sidebar.write("AI-Powered Personalized Education")

if menu == "Login":
    st.title("Login / Register")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Admin:**\n• `admin`\n• `AI_Learn2026!`")
    with col2:
        st.info("**Student:**\n• `khushi`\n• `Study2026!`")
    
    conn = get_connection()
    c = conn.cursor()
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
            result = c.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = result[0]
                st.session_state.menu = "Admin Panel" if result[0] == "admin" else "Main Dashboard"
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    with tab2:
        reg_username = st.text_input("New Username")
        reg_password = st.text_input("New Password", type="password")
        if st.button("Create Student Account"):
            try:
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                         (reg_username, reg_password, "student"))
                conn.commit()
                st.success("Student account created!")
            except:
                st.error("Username exists")
    
    conn.close()
    st.stop()

elif st.session_state.role == "admin" and menu == "Admin Panel":
    st.title("👥 Admin Panel - Complete Student Tracking")

    conn = get_connection()
    df_users = pd.read_sql("SELECT username FROM users WHERE role='student'", conn)
    df_logs = pd.read_sql("SELECT * FROM session_logs", conn)
    conn.close()

    total_students = len(df_users)
    total_quizzes = len(df_logs)
    avg_performance = df_logs["quiz_score"].mean()*10 if not df_logs.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", total_students)
    col2.metric("Total Quizzes Taken", total_quizzes)
    col3.metric("Average Performance", f"{avg_performance:.1f}%")

    # STUDENT TABLE
    student_data = []
    for student in df_users["username"]:
        logs = df_logs[df_logs["username"] == student]
        if not logs.empty:
            latest = logs.iloc[-1]
            student_data.append({
                "Student Name": student,
                "Grade/Class": latest.get("class_level", "N/A"),
                "Subject": latest["subject"],
                "Performance (%)": f"{latest['quiz_score']*10:.0f}%",
                "Quizzes Taken": len(logs),
                "Progress Level": latest["level"],
                "Learning Style": latest.get("learning_style", "Videos")
            })
        else:
            student_data.append({
                "Student Name": student,
                "Grade/Class": "N/A",
                "Subject": "N/A",
                "Performance (%)": "0%",
                "Quizzes Taken": 0,
                "Progress Level": "N/A",
                "Learning Style": "N/A"
            })

    df_students = pd.DataFrame(student_data)

    st.subheader("Registered Students")
    if not df_students.empty:
        subject_filter = st.selectbox(
            "Filter by Subject",
            ["All"] + sorted(df_students["Subject"].unique().tolist())
        )
        df_filtered = df_students
        if subject_filter != "All":
            df_filtered = df_students[df_students["Subject"] == subject_filter]
        st.dataframe(df_filtered, use_container_width=True, height=400)

        st.subheader("Performance Chart")
        chart_data = df_filtered.copy()
        chart_data["Performance_num"] = chart_data["Performance (%)"].str.replace("%","").astype(float)
        st.bar_chart(chart_data.set_index("Student Name")["Performance_num"])
    else:
        st.info("No students registered yet.")

elif st.session_state.role == "student" and menu == "Main Dashboard":
    st.title(f"🤖 AI-Powered Learning Platform - Welcome, {st.session_state.username}!")
    
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        with col1: 
            name = st.text_input("Student Name", value=st.session_state.username, disabled=True)
            class_level = st.selectbox("Select Class Level", ["Class 8", "Class 9", "Class 10", "Class 11", "Class 12"])
        with col2:
            subject = st.selectbox("Subject of Interest", list(QUIZ_LINKS.keys()))
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
        
        # SAVE TO DATABASE
        conn = get_connection()
        c = conn.cursor()
        quiz_score = performance / 10
        c.execute("""
            INSERT INTO session_logs 
            (username, class_level, subject, quiz_score, level, learning_style)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.username,
            class_level,
            subject,
            quiz_score,
            st.session_state.subject_levels.get(subject, "intermediate"),
            learning_style
        ))
        conn.commit()
        conn.close()

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
                # Demo video
                st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

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
            st.link_button(f"Start {subject} Quiz", quiz_link, use_container_width=True)
        
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

        # PREVIOUS ATTEMPTS
        st.markdown("### 📜 Previous Attempts")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT subject, level, quiz_score, class_level, timestamp
            FROM session_logs
            WHERE username=?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (st.session_state.username,))
        rows = c.fetchall()
        conn.close()

        if rows:
            df_history = pd.DataFrame(rows, columns=["Subject", "Level", "Quiz Score", "Class", "Time"])
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("📝 No previous attempts yet.")

        # ML FEEDBACK SECTION
        st.markdown("---")
        st.subheader("🤖 AI Adaptive Learning")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            feedback_rating = st.slider("Rate this content (1=Poor, 5=Excellent)", 1, 5, 3)
        with col2:
            st.metric("AI Level", level.title())

        if st.button("🚀 Train AI & Update Level", type="primary"):
            # SAVE FEEDBACK
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO session_logs (username, subject, level, quiz_score, rating)
                VALUES (?, ?, ?, ?, ?)
            """, (st.session_state.username, subject, level, score, feedback_rating))
            conn.commit()
            conn.close()

            # ML PROCESS
            st.info("🔄 Training AI model...")
            train_model()
            predicted_level = predict_level("General Learning", subject, "video", feedback_rating, score)
            
            if predicted_level:
                old_level = st.session_state.subject_levels[subject]
                st.session_state.subject_levels[subject] = predicted_level
                st.success(f"🤖 AI upgraded from **{old_level.title()}** → **{predicted_level.title()}**!")
                st.balloons()
            else:
                st.warning("ℹ️ Need more data for predictions")
            
            st.rerun()

        st.caption(f"**AI Status:** {subject}: {level.title()}")

elif menu == "Analytics":
    st.title("Analytics Dashboard")
    conn = get_connection()
    df_logs = pd.read_sql("SELECT * FROM session_logs", conn)
    conn.close()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Sessions", len(df_logs))
    col2.metric("Active Students", df_logs["username"].nunique() if not df_logs.empty else 0)
    
    st.bar_chart(df_logs["subject"].value_counts() if not df_logs.empty else pd.Series())

elif menu == "About":
    st.title("About AI Learning Platform")
    st.markdown("""
    **🎓 Features:**
    - **Admin**: Complete student tracking + analytics
    - **Students**: AI-powered personalized recommendations  
    - **Real-time**: ML model adapts to performance
    - **Multi-user**: Role-based dashboards
    
    **Admin sees**: Student table, metrics, charts
    **Student sees**: Learning recommendations, quizzes, videos, feedback
    """)
