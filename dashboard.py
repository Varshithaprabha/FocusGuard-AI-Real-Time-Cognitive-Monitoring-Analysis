import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
from sqlalchemy import create_engine
from src.db import get_sqlalchemy_url, authenticate_user

st.set_page_config(page_title="AI Study Helper Dashboard", layout="wide")

# Session State for Authentication
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

engine = create_engine(get_sqlalchemy_url())

def load_data(user_id=None, role='user'):
    try:
        if role == 'developer':
            # Developer sees all users' data
            summary_df = pd.read_sql_query("SELECT s.*, u.username FROM session_summary s JOIN users u ON s.user_id = u.id", engine)
            logs_df = pd.read_sql_query("SELECT l.*, u.username FROM session_logs l JOIN users u ON l.user_id = u.id", engine)
        else:
            # User sees only their data
            summary_df = pd.read_sql_query(f"SELECT * FROM session_summary WHERE user_id = {user_id}", engine)
            logs_df = pd.read_sql_query(f"SELECT * FROM session_logs WHERE user_id = {user_id}", engine)
        return summary_df, logs_df
    except Exception as e:
        st.error(f"Failed to connect to PostgreSQL: {e}")
        return None, None

def login_page():
    st.title("Welcome to AI Study Planner")
    st.subheader("Login to your Dashboard")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")
        
        if submit:
            user = authenticate_user(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['user_id'] = user[0]
                st.session_state['role'] = user[1]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
                
    st.markdown("---")
    st.info("Default Accounts:\n\n**Developer:** admin / admin123\n\n**User:** user1 / 1234")

def main_dashboard():
    # Sidebar
    st.sidebar.title(f"Hello, {st.session_state['username']}!")
    st.sidebar.write(f"Role: **{st.session_state['role'].capitalize()}**")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['user_id'] = None
        st.session_state['role'] = None
        st.rerun()

    st.title("🧠 AI Study Helper - Analytics Dashboard")

    summary_df, logs_df = load_data(st.session_state['user_id'], st.session_state['role'])

    if summary_df is None or summary_df.empty:
        st.warning("No session data found. Start a study session using the camera app first!")
    else:
        # Metrics
        st.sidebar.header("Overall Stats")
        total_sessions = len(summary_df)
        avg_score = summary_df['final_score'].mean()
        total_study_time = summary_df['focus_time'].sum()
        
        if st.session_state['role'] == 'developer':
            total_users = summary_df['user_id'].nunique()
            st.sidebar.metric("Total Active Users", total_users)

        st.sidebar.metric("Total Sessions", total_sessions)
        st.sidebar.metric("Average Focus Score", f"{avg_score:.1f}%")
        st.sidebar.metric("Total Focus Time (min)", f"{total_study_time:.1f}")

        # Charts Layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Focus Score Trends")
            # If developer, color by username
            color_arg = 'username' if st.session_state['role'] == 'developer' else None
            
            # Use start_time for x axis for better time series
            summary_df_sorted = summary_df.sort_values(by="start_time")
            fig_score = px.line(summary_df_sorted, x='start_time', y='final_score', color=color_arg, markers=True,
                                title='Focus Score over Time', labels={'start_time': 'Time', 'final_score': 'Score'})
            st.plotly_chart(fig_score, use_container_width=True)

        with col2:
            st.subheader("Overall Time Distribution")
            time_focus = summary_df['focus_time'].sum()
            time_distract = summary_df['distraction_time'].sum()
            time_absent = summary_df['absence_time'].sum()
            
            labels = ['Focus Time', 'Distraction Time', 'Absence Time']
            values = [time_focus, time_distract, time_absent]
            fig_pie = px.pie(names=labels, values=values, title='Global Breakdown')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Recent Sessions History")
        st.dataframe(summary_df.sort_values(by="start_time", ascending=False), use_container_width=True, hide_index=True)

        if not logs_df.empty:
            st.subheader("Live Log Timeline (Most Recent Session)")
            # Get the very last session
            last_sid = summary_df['session_id'].max()
            last_session_logs = logs_df[logs_df['session_id'] == last_sid]
            
            fig_timeline = px.scatter(last_session_logs, x='timestamp', y='state', color='state',
                                       title=f"Event Timeline for Session {last_sid} (Auto-updating)")
            st.plotly_chart(fig_timeline, use_container_width=True)

    # Auto-refresh the dashboard every 3 seconds for real-time live analytics
    if st.session_state['logged_in']:
        time.sleep(3)
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

if __name__ == "__main__":
    if not st.session_state['logged_in']:
        login_page()
    else:
        main_dashboard()
