# Simple Email Campaign Sender

A beginner-friendly Python project that implements a small email campaign pipeline with a Streamlit control UI. It's designed to send up to 100 emails per day in safe batches using a free Gmail account or a company SMTP server.

## Features

- **Safe Batch Sending**: Sends emails in configurable batches with delays to avoid spam filters.
- **Simple Configuration**: Uses environment variables for all settings.
- **Local Database**: Logs every send attempt to a local SQLite database for history tracking.
- **Streamlit UI**: A simple web interface to manage campaigns and view history.
- **GitHub Actions Integration**: Automate daily sending with a pre-configured workflow.
- **Beginner-Friendly**: Heavily commented code and clear instructions.

## Quickstart

### 1. Setup Your Environment

```bash
# Clone the repository
git clone https://github.com/your-username/simple-email-sender.git
cd simple-email-sender

# Create a virtual environment (we'll use .venv)
python -m venv .venv

# Activate it
# On Windows (Command Prompt):
.venv\Scripts\activate

# On Windows (PowerShell):
# If you see an error about running scripts being disabled, run this command in your terminal first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Then, activate the environment:
.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Settings

Copy the example environment file:

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in your details. The most important are your SMTP credentials.

**How to get a Gmail App Password:**
1. Go to your Google Account: `https://myaccount.google.com/`
2. Go to **Security** > **2-Step Verification** and enable it.
3. Go back to **Security** and click on **App passwords**.
4. Select `Other (Custom name)`, give it a name like `Python Email Sender`, and click `Generate`.
5. Copy the 16-character password and paste it into `SMTP_PASSWORD` in your `.env` file.

### 3. Run the Application

You can either use the Streamlit UI or run the sending script directly.

**Using the Streamlit UI:**

```bash
streamlit run streamlit_app.py
```

Open your browser to the URL provided by Streamlit. You can upload a CSV, write your email, and run the campaign locally.

**Using the Command Line:**

This is useful for testing or running from a server.

```bash
# Perform a dry run (builds messages but doesn't send)
python simple_email_sender.py data/sample_recipients.csv --dry-run

# Run the actual sending script
python simple_email_sender.py data/sample_recipients.csv
```

## Testing Plan

1.  **Create a Test CSV**: Create a file `data/test_recipients.csv` with 3 of your own email addresses.
2.  **Run a Dry Run**: Execute `python simple_email_sender.py data/test_recipients.csv --dry-run`. Check the console output to see if it processes the emails correctly.
3.  **Run a Live Test**: Execute `python simple_email_sender.py data/test_recipients.csv`. Check your inboxes to see if you received the emails.
4.  **Check the Database**: A `send_history.db` file should be created. You can use a tool like DB Browser for SQLite to open it and inspect the `sends` table.

## GitHub Actions for Automation

This project includes a GitHub Actions workflow in `.github/workflows/daily-send.yml` to automate sending emails daily.

### How to Set It Up

1.  **Push to GitHub**: Create a new repository on GitHub and push this project's code to it.
2.  **Add Secrets**: In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret** and add the following secrets:
    *   `SMTP_HOST`: e.g., `smtp.gmail.com`
    *   `SMTP_PORT`: e.g., `587`
    *   `SMTP_USER`: Your email address.
    *   `SMTP_PASSWORD`: Your 16-character app password.

### How It Works

-   The workflow is scheduled to run daily at 09:00 UTC.
-   You can also trigger it manually from the **Actions** tab in your repository.
-   It checks out the code, installs dependencies, and runs the `simple_email_sender.py` script using the secrets you provided.

## Where to Change Email Content

-   **Default Content**: You can change the default subject and body in `simple_email_sender.py` at the top of the script.
-   **Streamlit UI**: The UI provides text boxes to change the subject and body for each campaign you run.

## Important Notes

-   **Gmail Sending Limits**: Free Gmail accounts have a sending limit (typically around 100-500 emails per day). Be mindful of this and start with low numbers.
-   **Unsubscribe Link**: The `{unsubscribe_link}` is a placeholder. For a real application, you would need to build a web endpoint that handles unsubscribe requests.
-   **Security**: Never commit your `.env` file with your credentials to Git. The `.gitignore` file should already be configured to prevent this.
