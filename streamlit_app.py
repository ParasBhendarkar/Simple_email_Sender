# streamlit_app.py
# This script provides a simple UI for the email campaign tool.
# It allows users to upload a recipient list, compose an email, and view send history.

import streamlit as st
import pandas as pd
import sqlite3
import os
from simple_email_sender import run_campaign, setup_database, truncate_database

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
# Initialize the database
setup_database()

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
    if st.button('🚀 Run Campaign', help='This will start the email sending process.'):
        with st.spinner('Sending emails... Please wait.'):
            # Set environment variables for the campaign
            os.environ['TOTAL_PER_DAY'] = str(total_per_day)
            os.environ['BATCH_SIZE'] = str(batch_size)
            os.environ['BATCH_INTERVAL_SEC'] = str(batch_interval * 60)

            # Run the campaign
            run_campaign(recipients_df, subject, body_template)
            st.success('Campaign finished! Check the History tab for results.')
            # Automatically rerun to refresh the history
            st.rerun()

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

    col1, col2 = st.columns([1, 0.2])
    with col1:
        if st.button('Refresh History'):
            st.rerun()
    with col2:
        if st.button('Clear History'):
            truncate_database()
            st.success('Send history has been cleared.')
            st.rerun()
