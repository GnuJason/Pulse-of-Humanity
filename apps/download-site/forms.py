"""Contact form, CAPTCHA generation, and email dispatch."""

import os
import random
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(message="Name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=200, message="Email must be less than 200 characters")
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(message="Message is required"),
        Length(min=10, max=2000, message="Message must be between 10 and 2000 characters")
    ])
    captcha_answer = IntegerField('Math Captcha', validators=[
        DataRequired(message="Please solve the math problem")
    ])


def generate_captcha():
    """Generate a simple math captcha (addition/subtraction)."""
    operation = random.choice(['+', '-'])
    if operation == '+':
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = a + b
        question = f"{a} + {b}"
    else:
        a, b = random.randint(10, 30), random.randint(1, 10)
        answer = a - b
        question = f"{a} - {b}"

    return question, answer


def send_contact_email(name, email, message):
    """Send contact form data via SMTP."""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.mailfence.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        recipient_email = os.getenv('RECIPIENT_EMAIL')

        if not all([smtp_username, smtp_password, recipient_email]):
            raise ValueError("Missing SMTP configuration in environment variables")

        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = recipient_email
        msg['Subject'] = f"Contact Form Submission from {name}"

        body = f"""
New contact form submission from Pulse of Humanity:

Name: {name}
Email: {email}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{message}

---
This message was sent from the contact form on your Pulse of Humanity website.
Reply directly to this email to respond to {name} at {email}.
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

        return True, "Email sent successfully"

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False, str(e)
