"""
FitBot Marketing Email Script
Sends a personalized re-engagement + referral email to every user in the `users` table.

Run this LOCALLY on your machine (not on Cloud Run) since it's a one-off script,
not something that needs to run 24/7 as part of the app.

Requires: psycopg2, and the two env vars below to be set before running.
"""

import os
import time
import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---- CONFIG ----
DATABASE_URL = os.environ.get("DATABASE_URL")
GMAIL_USER = "fitbot.ai31@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

SUBJECT = "We miss you at FitBot 💪 (plus a favor to ask)"

BODY_TEMPLATE = """Hey {username},

It's been a bit since we've seen you on FitBot — hope life's been good!

Just a quick update: we recently upgraded our servers to be faster and more reliable, so your workout plans, diet advice, and chat replies now load quicker than ever.

If you've got a few minutes today, come back and pick up where you left off:
https://fitbot-402357265699.asia-south1.run.app

Also — a small ask. FitBot is built and run by just one person (hi, that's me), and the best way it grows is through people like you. If FitBot has helped you even a little, would you mind sharing it with a friend or family member who's trying to get fit? Just forward them the link above.

Every share genuinely helps.

Thanks for being one of our early users — it means a lot.

Ibrahim
Founder, FitBot

---
If you'd rather not receive emails like this, just reply with "unsubscribe" and we won't email you again.
"""


def get_users():
    """Fetch username and email for all users in the database."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT username, email FROM users WHERE email IS NOT NULL;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def send_email(smtp_server, to_email, username):
    """Send one personalized email."""
    msg = MIMEMultipart()
    msg["From"] = f"FitBot <{GMAIL_USER}>"
    msg["To"] = to_email
    msg["Subject"] = SUBJECT

    body = BODY_TEMPLATE.format(username=username)
    msg.attach(MIMEText(body, "plain"))

    smtp_server.sendmail(GMAIL_USER, to_email, msg.as_string())


def main():
    if not DATABASE_URL:
        raise SystemExit("ERROR: DATABASE_URL environment variable not set.")
    if not GMAIL_APP_PASSWORD:
        raise SystemExit("ERROR: GMAIL_APP_PASSWORD environment variable not set.")

    users = get_users()
    print(f"Found {len(users)} users to email.\n")

    # Confirm before sending — safety check so you don't blast emails by accident
    confirm = input(f"About to send emails to {len(users)} users. Type 'yes' to continue: ")
    if confirm.strip().lower() != "yes":
        print("Aborted. No emails sent.")
        return

    smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_server.starttls()
    smtp_server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

    sent = 0
    failed = []

    for username, email in users:
        try:
            send_email(smtp_server, email, username)
            sent += 1
            print(f"[{sent}/{len(users)}] Sent to {email}")
            time.sleep(2)  # small delay to avoid rate limits / spam flags
        except Exception as e:
            print(f"FAILED to send to {email}: {e}")
            failed.append(email)

    smtp_server.quit()

    print(f"\nDone. Sent: {sent}, Failed: {len(failed)}")
    if failed:
        print("Failed addresses:", failed)


if __name__ == "__main__":
    main()