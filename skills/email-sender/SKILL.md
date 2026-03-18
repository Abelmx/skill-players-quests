---
name: email-sender
description: Send emails via SMTP. Use when the user asks to send, compose, or draft emails to recipients.
---

# Email Sender

## Instructions

When the user asks to send an email:

1. Set required environment variables: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`
2. Run the script:
   ```bash
   python scripts/send_email.py --to "recipient@example.com" --subject "Subject" --body "Body text"
   ```

3. The script uses smtplib to send via SMTP.

## Notes

- Requires SMTP_HOST, SMTP_USER, SMTP_PASS environment variables.
- Exits with an error if credentials are not configured.
