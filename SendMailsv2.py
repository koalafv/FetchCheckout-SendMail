import os
import sys
import smtplib
import sqlite3
import logging
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- KONFIGURACJA ---
load_dotenv()

# Ustawienie kodowania dla Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_service.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("LuxmodeMailer")

class EmailDatabase:
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
        self.smtp_connection = None
        
        self.stats = {"sent": 0, "skipped": 0, "failed": 0}

    def _connect_smtp(self):
        """Nawiązuje połączenie z serwerem."""
        try:
            self.smtp_connection = smtplib.SMTP_SSL(self.smtp_host, 465)
            self.smtp_connection.login(self.user, self.password)
            return True
        except Exception as e:
            logger.error(f"🔌 Błąd łączenia z serwerem: {e}")
            return False

    def _ensure_connection(self):
        """Sprawdza czy połączenie żyje, jak nie to wznawia."""
        try:
            status = self.smtp_connection.noop()[0]
            if status != 250:
                raise Exception("Noop failed")
        except:
            logger.warning("🔌 Utracono połączenie. Wznawiam...")
            return self._connect_smtp()
        return True

    def _prepare_html(self, template_path: str, context: Dict[str, str]) -> str:
        path = Path(template_path)
        if not path.exists():
            raise FileNotFoundError(f"Brak szablonu: {template_path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for key, value in context.items():
            content = content.replace(f"[{key}]", str(value))
        return content

    def send_single_email(self, email: str, url: str, subject: str, template_path: str) -> str:
        # 1. Walidacja
        invalid_markers = ['none', 'brak', 'null', 'undefined', 'error']
        if not email or '@' not in email or any(m in email.lower() for m in invalid_markers):
            return "skipped", "Nieprawidłowy adres"

        # 2. Duplikaty
        if self.db.check_if_sent(email, subject):
            return "skipped", "Już wysłano"

        # 3. Wysyłka
        simple_name = email.split('@')[0]
        context = {"imie": simple_name, "adres e-mail": email, "url_koszyka": url}

        try:
            self._ensure_connection() # Upewnij się, że mamy rurę do serwera
            
            html_content = self._prepare_html(template_path, context)
            text_content = f"Dokończ zakupy: {url}"

            msg = MIMEMultipart("alternative")
            msg['Subject'] = subject
            msg['From'] = f"Luxmode Sklep <{self.user}>"
            msg['To'] = email
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            self.smtp_connection.send_message(msg)
            
            self.db.mark_as_sent(email, subject)
            return "sent", "OK"

        except Exception as e:
            # Jeśli błąd krytyczny połączenia, spróbuj raz jeszcze po restarcie
            time.sleep(2)
            try:
                self._connect_smtp()
                self.smtp_connection.send_message(msg)
                self.db.mark_as_sent(email, subject)
                return "sent", "OK (po resecie)"
            except Exception as e2:
                return "failed", str(e2)

    def send_campaign(self, input_file: str, subject: str, template_path: str):
        if not os.path.exists(input_file):
            print(f"❌ Plik {input_file} nie istnieje.")
            return

        # Wczytywanie
        tasks = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    email, url = line.strip().split(':', 1)
                    tasks.append((email.strip(), url.strip()))

        total = len(tasks)
        print(f"🚀 Rozpoczynam kampanię dla {total} maili (Tryb: Safe Sequence)...")
        
        # Otwórz połączenie raz na początku
        if not self._connect_smtp():
            print("❌ Nie można połączyć się z serwerem SMTP. Sprawdź .env.")
            return

        pbar = tqdm(tasks, unit="mail", colour="green", dynamic_ncols=True)
        
        for email, url in pbar:
            status, msg = self.send_single_email(email, url, subject, template_path)
            
            self.stats[status] += 1
            
            if status == "sent":
                logger.info(f"✅ Sent: {email}")
                pbar.set_description(f"Wysłano: {email}")
                # WAŻNE: Pauza dla bezpieczeństwa
                time.sleep(1.0) 
                
            elif status == "skipped":
                logger.info(f"⏭️ Skipped: {email} ({msg})")
                
            elif status == "failed":
                logger.error(f"❌ Failed: {email} - {msg}")
                tqdm.write(f"❌ Błąd: {email} ({msg})")
                pbar.set_description(f"Błąd: {email}")
                time.sleep(2.0) # Dłuższa przerwa po błędzie

        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except:
                pass

        print("\n" + "="*35)
        print("📊 RAPORT KOŃCOWY")
        print("="*35)
        print(f"✅ Wysłanych:   {self.stats['sent']}")
        print(f"⏭️ Pominiętych: {self.stats['skipped']}")
        print(f"❌ Błędów:      {self.stats['failed']}")
        print("="*35)

if __name__ == "__main__":
    manager = EmailManager()
    manager.send_campaign(
        input_file="results.txt", 
        subject="Twój koszyk czeka w LuxMode (kod: hjzb4z) 🎁",
        template_path="email_template.html" 
    )