import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_faq_notification(email_user, question):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    dest_email = os.getenv("EMAIL_DESTINATAIRE", smtp_user)

    if not smtp_password:
        print("⚠️ ERREUR: Pas de mot de passe email dans .env")
        return

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = dest_email
    msg["Subject"] = f"🆕 Question FAQ de {email_user}"
    
    body = f"👤 Email: {email_user}\n\n❓ Question:\n{question}"
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email envoyé à {dest_email}")
    except Exception as e:
        print(f"❌ Erreur Email: {e}")