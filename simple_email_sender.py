# simple_email_sender.py
# This script sends emails to a list of recipients from a CSV file.
# It uses environment variables for configuration and logs the send history to a SQLite database.

import os # Used to access environment variables.
import smtplib # Used to send emails using the Simple Mail Transfer Protocol (SMTP).
import ssl # Provides SSL/TLS support for secure connections.
import time # Used to add delays between sending emails.
import argparse # Used to parse command-line arguments.
import pandas as pd # Used to read and process CSV files.
import sqlite3 # Used for the SQLite database to log email history.
from email.message import EmailMessage # Used to create email messages.
from dotenv import load_dotenv # Used to load environment variables from a .env file.

# Load environment variables from .env file
load_dotenv() # This function loads variables from a .env file into the environment.

# --- Configuration ---
FROM_NAME = os.getenv('FROM_NAME', 'Your Name') # The name that will appear as the sender.
FROM_EMAIL = os.getenv('FROM_EMAIL', 'your_email@example.com') # The email address that will be used to send emails.
DEFAULT_SUBJECT = 'Hello from Your Company!' # The default subject line for the emails.
DEFAULT_BODY_TEMPLATE = 'Hi {name},\n\nThis is a test email.\n\nBest regards,\n{company_name}' # The template for the email body.

# --- Database Setup ---
DB_FILE = 'send_history.db' # The name of the SQLite database file.

def setup_database():
    """Create the sends table in the SQLite database if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE) # Connect to the SQLite database.
    cursor = conn.cursor() # Create a cursor object to execute SQL commands.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            name TEXT,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT
        )
    ''') # SQL command to create a table named 'sends' if it doesn't already exist.
    conn.commit() # Save the changes to the database.
    conn.close() # Close the connection to the database.

def log_send(email, name, status, error_message=None):
    """Log the result of an email send to the database."""
    conn = sqlite3.connect(DB_FILE) # Connect to the SQLite database.
    cursor = conn.cursor() # Create a cursor object to execute SQL commands.
    cursor.execute('''
        INSERT INTO sends (email, name, status, error_message)
        VALUES (?, ?, ?, ?)
    ''', (email, name, status, error_message)) # SQL command to insert a new record into the 'sends' table.
    conn.commit() # Save the changes to the database.
    conn.close() # Close the connection to the database.

def truncate_database():
    """Delete all records from the sends table."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sends')
    conn.commit()
    conn.close()

# --- Email Sending Logic ---
def create_message(recipient_email, recipient_name, subject, body_template):
    """Create an EmailMessage object."""
    msg = EmailMessage() # Create a new EmailMessage object.
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>' # Set the sender's name and email address.
    msg['To'] = recipient_email # Set the recipient's email address.
    msg['Subject'] = subject # Set the subject of the email.

    # Personalize the body
    body = body_template.format( # Format the body template with personalized information.
        name=recipient_name or 'there', # Use the recipient's name, or 'there' if no name is provided.
        company_name=os.getenv('COMPANY_NAME', 'Your Company'), # Get the company name from environment variables.
        unsubscribe_link=os.getenv('UNSUBSCRIBE_LINK', '#') # Get the unsubscribe link from environment variables.
    )
    msg.set_content(body) # Set the plain text content of the email.
    return msg # Return the created EmailMessage object.

def send_batch(recipients, subject, body_template, dry_run=False):
    """Send a batch of emails using a single SMTP connection."""
    smtp_host = os.getenv('SMTP_HOST') # Get the SMTP server host from environment variables.
    smtp_port = int(os.getenv('SMTP_PORT', 587)) # Get the SMTP server port from environment variables.
    smtp_user = os.getenv('SMTP_USER') # Get the SMTP username from environment variables.
    smtp_password = os.getenv('SMTP_PASSWORD') # Get the SMTP password from environment variables.
    per_email_delay = float(os.getenv('PER_EMAIL_DELAY_SEC', 1.0)) # Get the delay between sending emails from environment variables.

    if not all([smtp_host, smtp_port, smtp_user, smtp_password]): # Check if all required SMTP settings are configured.
        print('Error: SMTP settings are not configured in environment variables.') # Print an error message if settings are missing.
        return # Exit the function.

    context = ssl.create_default_context() # Create a default SSL context for a secure connection.
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server: # Create an SMTP server object.
            server.starttls(context=context) # Upgrade the connection to a secure TLS connection.
            server.login(smtp_user, smtp_password) # Log in to the SMTP server.
            print(f'Successfully connected to SMTP server for batch.') # Print a success message.

            for _, row in recipients.iterrows(): # Iterate over each recipient in the batch.
                email = row['email'] # Get the recipient's email address.
                name = row.get('name') # Get the recipient's name (if available).

                print(f'Processing email to: {email}') # Print a message indicating which email is being processed.
                if dry_run: # Check if this is a dry run.
                    print(f'  [DRY RUN] Would send to {email}') # Print a message indicating a simulated send.
                    log_send(email, name, 'dry-run') # Log the dry run to the database.
                    time.sleep(0.1) # Simulate work
                    continue # Skip to the next recipient.

                # Simple retry mechanism
                for attempt in range(3): # Loop to retry sending the email up to 3 times.
                    try:
                        message = create_message(email, name, subject, body_template) # Create the email message.
                        server.send_message(message) # Send the email message.
                        print(f'  Successfully sent to {email}') # Print a success message.
                        log_send(email, name, 'sent') # Log the successful send to the database.
                        break # Exit the retry loop on success.
                    except Exception as e: # Catch any exceptions that occur during sending.
                        print(f'  Attempt {attempt + 1} failed for {email}: {e}') # Print an error message.
                        if attempt < 2: # If this is not the last attempt.
                            time.sleep(2 ** attempt) # Wait for a while before retrying (exponential backoff).
                        else: # If this is the last attempt.
                            log_send(email, name, 'failed', str(e)) # Log the failed send to the database.
                time.sleep(per_email_delay) # Wait for the specified delay before sending the next email.

    except smtplib.SMTPAuthenticationError as e: # Catch SMTP authentication errors.
        print(f'SMTP Authentication Error: {e}. Check your SMTP_USER and SMTP_PASSWORD.') # Print an error message.
        for _, row in recipients.iterrows(): # Iterate over the recipients in the batch.
            log_send(row['email'], row.get('name'), 'failed', 'SMTP Authentication Error') # Log the failure for each recipient.
    except Exception as e: # Catch any other exceptions.
        print(f'An error occurred during batch send: {e}') # Print a general error message.
        for _, row in recipients.iterrows(): # Iterate over the recipients in the batch.
            log_send(row['email'], row.get('name'), 'failed', str(e)) # Log the failure for each recipient.

# --- Main Script Logic ---
def run_campaign(recipients_df, subject, body_template, dry_run=False):
    """Main logic to run an email campaign.

    Args:
        recipients_df (pd.DataFrame): DataFrame with recipient data, must include 'email' column.
        subject (str): The subject of the email.
        body_template (str): The body template for the email.
        dry_run (bool): If True, simulates sending without actually sending emails.
    """
    # --- Configuration from environment variables ---
    total_per_day = int(os.getenv('TOTAL_PER_DAY', 100))
    batch_size = int(os.getenv('BATCH_SIZE', 20))
    batch_interval = int(os.getenv('BATCH_INTERVAL_SEC', 600))

    # --- Load and prepare recipients ---
    if 'email' not in recipients_df.columns:
        print('Error: DataFrame must have an "email" column.')
        return

    # Get recipients that have not been sent to today
    conn = sqlite3.connect(DB_FILE)
    try:
        today_sent_df = pd.read_sql_query(
            "SELECT email FROM sends WHERE status IN ('sent', 'dry-run') AND date(timestamp) = date('now')",
            conn
        )
    except pd.io.sql.DatabaseError:
        today_sent_df = pd.DataFrame(columns=['email'])
    finally:
        conn.close()

    recipients_to_send = recipients_df[~recipients_df['email'].isin(today_sent_df['email'])]
    recipients_to_send = recipients_to_send.head(total_per_day)

    if recipients_to_send.empty:
        print('No new recipients to send to today.')
        return

    print(f'Found {len(recipients_to_send)} emails to send.')

    # --- Process in batches ---
    num_batches = (len(recipients_to_send) + batch_size - 1) // batch_size
    for i in range(num_batches):
        start_index = i * batch_size
        end_index = start_index + batch_size
        batch_df = recipients_to_send.iloc[start_index:end_index]

        print(f'\n--- Starting Batch {i + 1}/{num_batches} ---')
        send_batch(batch_df, subject, body_template, dry_run)

        if i < num_batches - 1:
            print(f'--- Batch finished. Waiting for {batch_interval} seconds... ---')
            time.sleep(batch_interval)

    print('\nAll batches processed.')


def main():
    """Main function to run the email sending script from the command line."""
    parser = argparse.ArgumentParser(description='Send emails from a CSV file.')
    parser.add_argument('csv_file', help='Path to the CSV file with recipient data.')
    parser.add_argument('--dry-run', action='store_true', help='Simulate sending without actually sending emails.')
    args = parser.parse_args()

    try:
        recipients_df = pd.read_csv(args.csv_file)
    except FileNotFoundError:
        print(f'Error: The file {args.csv_file} was not found.')
        return

    run_campaign(recipients_df, DEFAULT_SUBJECT, DEFAULT_BODY_TEMPLATE, args.dry_run)

if __name__ == '__main__': # Check if the script is being run directly.
    setup_database() # Set up the database.
    main() # Run the main function.
