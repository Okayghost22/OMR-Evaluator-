import streamlit as st
import os
import json
import uuid
import io
import csv
import sqlite3
import pandas as pd
from datetime import datetime
from omr_processor import process_omr_sheet

# === Database Functions ===
DB_FILE = "results.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS omr_result (
            id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            exam_set TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            subject_scores TEXT NOT NULL,
            answers TEXT NOT NULL,
            annotated_image_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_result_to_db(result_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO omr_result (filename, exam_set, total_score, subject_scores, answers, annotated_image_path) VALUES (?, ?, ?, ?, ?, ?)",
        (
            result_data['filename'],
            result_data['exam_set'],
            result_data['total_score'],
            json.dumps(result_data['subject_scores']),
            json.dumps(result_data['answers']),
            result_data['annotated_image_path']
        )
    )
    conn.commit()
    conn.close()

def get_all_results():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM omr_result", conn)
    conn.close()
    return df

# === User Session State ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# === Navigation ===
def navigate_to(page):
    st.session_state.page = page

# === UI Pages ===
def home_page():
    st.title("OMR Evaluator")
    
    st.markdown("""
    Upload an OMR sheet image to get a real-time evaluation. The results will be stored and
    can be viewed later from the dashboard.
    """)

    with st.form("upload_form", clear_on_submit=False):
        exam_set = st.selectbox("Select Exam Set:", ("set_a", "set_b"))
        uploaded_file = st.file_uploader("Upload OMR Sheet Image:", type=["png", "jpg", "jpeg"])
        submit_button = st.form_submit_button("Evaluate")

    if submit_button and uploaded_file is not None:
        with st.spinner('Processing your OMR sheet...'):
            # Save the uploaded file temporarily
            upload_folder = "uploads"
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            unique_filename = str(uuid.uuid4()) + "_" + uploaded_file.name
            file_path = os.path.join(upload_folder, unique_filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process the OMR sheet
            result = process_omr_sheet(file_path, exam_set)

            if result["status"] == "success":
                # Save to database
                annotated_path = os.path.basename(result["annotated_image_path"])
                db_result = {
                    'filename': unique_filename,
                    'exam_set': exam_set,
                    'total_score': result["total_score"],
                    'subject_scores': result["subject_scores"],
                    'answers': result["answers"],
                    'annotated_image_path': annotated_path
                }
                save_result_to_db(db_result)

                # Store the result in session state to display on the results page
                st.session_state.last_result = db_result
                navigate_to('results')
            else:
                st.error(f"Error: {result['message']}")
    
    st.markdown("---")
    if st.button("Go to Admin Dashboard"):
        navigate_to('login')

def results_page():
    st.title("Evaluation Results")
    
    if 'last_result' in st.session_state:
        result_data = st.session_state.last_result
        
        st.subheader(f"Total Score: {result_data['total_score']}")
        
        # Display Subject Scores
        st.subheader("Subject-wise Scores")
        subject_df = pd.DataFrame(result_data['subject_scores'].items(), columns=['Subject', 'Score'])
        st.dataframe(subject_df, hide_index=True)
        
        # Display Answer Key
        st.subheader("Answer Sheet")
        answers_df = pd.DataFrame.from_dict(result_data['answers'], orient='index')
        answers_df.index.name = 'Question'
        st.dataframe(answers_df)

        st.subheader("Annotated OMR Sheet")
        annotated_image_path = os.path.join("uploads", result_data['annotated_image_path'])
        if os.path.exists(annotated_image_path):
            st.image(annotated_image_path)
        else:
            st.warning("Annotated image not found.")
            
    else:
        st.info("No results to display. Please upload a sheet from the home page.")

    if st.button("Evaluate another sheet"):
        navigate_to('home')

def login_page():
    st.title("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "evaluator" and password == "password123":
            st.session_state.logged_in = True
            navigate_to('dashboard')
            st.success("Logged in successfully!")
            st.rerun() # Rerun to refresh the page
        else:
            st.error("Invalid credentials")
    
    if st.button("Back to Home"):
        navigate_to('home')

def dashboard_page():
    st.title("Admin Dashboard")
    
    if not st.session_state.logged_in:
        navigate_to('login')
        st.stop()
        
    st.subheader("Evaluated OMR Sheets")
    
    all_results = get_all_results()
    
    if not all_results.empty:
        st.dataframe(all_results, use_container_width=True)
        
        # CSV Export
        @st.cache_data
        def convert_df_to_csv(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv(index=False).encode('utf-8')

        csv_file = convert_df_to_csv(all_results)
        st.download_button(
            label="Download data as CSV",
            data=csv_file,
            file_name='omr_results.csv',
            mime='text/csv',
        )
    else:
        st.info("No sheets have been evaluated yet.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        navigate_to('home')
        st.rerun()
        
# === Main App Logic ===
if __name__ == "__main__":
    init_db()
    
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()
    elif st.session_state.page == 'results':
        results_page()
