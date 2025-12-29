import os
import sys
import smtplib
import sqlite3
import logging
import time
from pathlib import Path
from typing import Dict

# Email libraries
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
# --- Configuration ---
load_dotenv() 

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # FIX: Dodanie encoding='utf-8' do pliku logów
        logging.FileHandler("email_service.log", encoding='utf-8'), 
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LuxmodeMailer")

class EmailDatabase:
    """Prevents duplicate sends."""
    def __init__(self, db_path: str = 'emails.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sent_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT,
                    subject TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(recipient, subject)
                )
            ''')

    def check_if_sent(self, recipient: str, subject: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM sent_history WHERE recipient = ? AND subject = ?", 
                (recipient, subject)
            )
            return cursor.fetchone() is not None

    def mark_as_sent(self, recipient: str, subject: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sent_history (recipient, subject) VALUES (?, ?)", 
                (recipient, subject)
            )

class EmailManager:
    def __init__(self):
        self.user = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASS')
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.db = EmailDatabase()

        if not self.user or not self.password:
            logger.warning("⚠️ WARNING: Missing env variables. Check .env file.")

    def _prepare_html(self, template_path: str, context: Dict[str, str]) -> str:
        """Loads HTML and replaces placeholders like [url_koszyka]"""
        path = Path(template_path)
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for key, value in context.items():
            content = content.replace(f"[{key}]", str(value))
            
        return content

    def send_html_email(self, to_email: str, subject: str, template_path: str, context: Dict[str, str]):
        try:
            html_content = self._prepare_html(template_path, context)
            
            # Plain text fallback
            text_content = f"Witaj,\nDokończ zakupy tutaj: {context.get('url_koszyka', 'https://luxmode.pl')}"

            msg = MIMEMultipart("alternative")
            msg['Subject'] = subject
            msg['From'] = f"Luxmode Sklep <{self.user}>"
            msg['To'] = to_email

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL(self.smtp_host, 465) as smtp:
                smtp.login(self.user, self.password)
                smtp.send_message(msg)
                
            logger.info(f"✅ Sent to: {to_email}")
            self.db.mark_as_sent(to_email, subject)

        except Exception as e:
            logger.error(f"❌ Failed to send to {to_email}: {e}")

    def send_campaign_from_txt(self, input_file: str, subject: str, template_path: str):
        """Reads 'email:url' format and sends emails."""
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        logger.info(f"🚀 Starting campaign for {len(lines)} lines...")

        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue

            # Split only on the FIRST colon (because URLs contain colons like http:)
            email, url = line.split(':', 1)
            email = email.strip()
            url = url.strip()

            # 1. Check DB
            if self.db.check_if_sent(email, subject):
                logger.info(f"⏭️ Skipped {email} - already sent.")
                continue

            # 2. Create Context (Data for the email)
            # extracting a "name" from email (e.g., "john" from "john@gmail.com") for [imie]
            simple_name = email.split('@')[0]
            
            context = {
                "imie": simple_name,     # Replaces [imie]
                "adres e-mail": email,   # Replaces [adres e-mail]
                "url_koszyka": url,      # Replaces [url_koszyka] <-- CRITICAL UPDATE
            }
            
            # 3. Send
            self.send_html_email(email, subject, template_path, context)
            
            # 4. Anti-spam delay
            # time.sleep(0.2) 

        logger.info("🏁 Campaign finished.")

if __name__ == "__main__":
    manager = EmailManager()
    
    # Ensure 'results.txt' exists (generated by your previous script)
    # Ensure 'szablon.html' exists
    manager.send_campaign_from_txt(
        input_file="results.txt", 
        subject="Twój koszyk czeka w LuxMode (kod: hjzb4z) 🎁",
        template_path="email_template.html" 
    )