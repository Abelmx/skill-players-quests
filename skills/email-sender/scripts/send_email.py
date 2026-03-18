#!/usr/bin/env python3
"""Send email via SMTP. Requires SMTP_HOST, SMTP_USER, SMTP_PASS env vars."""
import argparse
import os
import smtplib
import sys
from email.mime.text import MIMEText


def main():
    parser = argparse.ArgumentParser(description="Send email via SMTP")
    parser.add_argument("--to", "-t", required=True, help="Recipient email address")
    parser.add_argument("--subject", "-s", required=True, help="Email subject")
    parser.add_argument("--body", "-b", required=True, help="Email body")
    args = parser.parse_args()

    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")

    if not all([host, user, password]):
        print("Error: Set SMTP_HOST, SMTP_USER, SMTP_PASS environment variables", file=sys.stderr)
        sys.exit(1)

    msg = MIMEText(args.body)
    msg["Subject"] = args.subject
    msg["From"] = user
    msg["To"] = args.to

    with smtplib.SMTP(host) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(user, args.to, msg.as_string())
    print("Email sent successfully")


if __name__ == "__main__":
    main()
