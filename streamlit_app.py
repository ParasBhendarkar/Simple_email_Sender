# streamlit_app.py
# This script provides a simple UI for the email campaign tool.
# It allows users to upload a recipient list, compose an email, and view send history.

import streamlit as st
import pandas as pd
import sqlite3
import os
import subprocess

# --- Configuration ---
DB_FILE = 'send_history.db'
SAMPLE_CSV = 'data/sample_recipients.csv'

# --- Helper Functions ---
def get_send_history():
    """Fetch the last 50 records from the send history database."""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    try:
        history_df = pd.read_sql_query('SELECT * FROM sends ORDER BY timestamp DESC LIMIT 50', conn)
    except pd.io.sql.DatabaseError:
        return pd.DataFrame() # Return empty if table doesn't exist yet
    finally:
        conn.close()
    return history_df

# --- Streamlit UI ---
st.set_page_config(page_title='Simple Email Sender', layout='wide')
st.title('✉️ Simple Email Campaign Sender')

tab1, tab2 = st.tabs(['Campaign', 'History'])

# --- Campaign Tab ---
with tab1:
    st.header('🚀 Launch a New Campaign')

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('1. Recipients')
        uploaded_file = st.file_uploader('Upload a CSV file with `email` and `name` columns.', type=['csv'])
        
        if uploaded_file:
            recipients_df = pd.read_csv(uploaded_file)
            st.success(f'Loaded {len(recipients_df)} recipients.')
        else:
            st.info(f'No file uploaded. Using sample data: `{SAMPLE_CSV}`')
            recipients_df = pd.read_csv(SAMPLE_CSV)
        
        st.write('**Preview:**')
        st.dataframe(recipients_df.head(10))

    with col2:
        st.subheader('2. Email Content')
        subject = st.text_input('Subject', 'Your Daily Newsletter')
        body_template = st.text_area(
            'Body (use {name} for personalization)',
            'Hi {name},\n\nThis is your daily update!\n\nCheers,\nYour Company',
            height=200
        )
        st.markdown('You can also use `{company_name}` and `{unsubscribe_link}`.')

    st.subheader('3. Sending Configuration')
    c1, c2, c3 = st.columns(3)
    total_per_day = c1.number_input('Total Emails per Day', min_value=1, value=100)
    batch_size = c2.number_input('Batch Size', min_value=1, value=20)
    batch_interval = c3.number_input('Interval Between Batches (minutes)', min_value=1, value=10)

    st.subheader('4. Launch!')
    if st.button('🚀 Run Locally (for testing)', help='This runs the sender script in the background.'):
        # For a real app, you'd use a task queue like Celery or RQ.
        # This is a simplified approach for local development.
        st.warning('Starting the sending process. This may take a while. Check your console for logs.')
        
        # Set environment variables for the script
        env = os.environ.copy()
        env['TOTAL_PER_DAY'] = str(total_per_day)
        env['BATCH_SIZE'] = str(batch_size)
        env['BATCH_INTERVAL_SEC'] = str(batch_interval * 60)
        
        # Determine which CSV to use
        csv_path = SAMPLE_CSV
        if uploaded_file:
            # Save the uploaded file temporarily to be used by the script
            temp_csv_path = os.path.join('data', 'temp_recipients.csv')
            with open(temp_csv_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            csv_path = temp_csv_path

        process = subprocess.Popen(
            ['python', 'simple_email_sender.py', csv_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        st.success('Sender script started. See the terminal where you launched Streamlit for progress.')
        st.info('The UI will not update in real-time. Refresh the History tab to see results.')

    st.markdown('---')
    st.info(
        '**Production Usage:** For reliable sending, use the GitHub Actions workflow. ' 
        'Running the sender from the Streamlit app is only for development and testing.'
    )

# --- History Tab ---
with tab2:
    st.header('📜 Send History')
    st.write('Showing the last 50 sends.')
    
    history_df = get_send_history()
    if history_df.empty:
        st.warning('No send history found. Run a campaign to see results here.')
    else:
        st.dataframe(history_df)

    if st.button('Refresh History'):
        st.rerun()
