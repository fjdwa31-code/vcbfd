import threading
import email
import requests
import logging
import time
from datetime import datetime, timezone
from imapclient import IMAPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── FILL THESE IN ──────────────────────────────────────────
N8N_WEBHOOK_URL = "https://fbhdsa.app.n8n.cloud/webhook/dc0d0625-d17f-4876-aa4b-6662a5ef16bd"

IMAP_HOST = "mail.privateemail.com"
IMAP_PORT = 993

INBOXES = [
    {"email": "nuel.c@botcipherco.site", "password": "ZkDx6/btSAS6}:^"},
    {"email": "nuel1@botcipherhq.site", "password": "wZ9szX%w6fQWTCv"},
    {"email": "nuel.co@botcipherhq.site", "password": "X9dc^:.wBM)Y:cb"},
    {"email": "nuel@botcipherai.site", "password": "i(Vx8gc;YCsQrj;"},
    {"email": "nuel.o@botcipherai.site", "password": "YF%}M6}Uc^?dvt2"},
]
# ───────────────────────────────────────────────────────────

def parse_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
    return msg.get_payload(decode=True).decode(errors="ignore")

def send_to_n8n(data):
    try:
        requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
        logging.info(f"Sent to n8n: {data['subject']} from {data['from']}")
    except Exception as e:
        logging.error(f"Failed to send to n8n: {e}")

def watch_inbox(config):
    while True:
        try:
            logging.info(f"Connecting to {config['email']}...")
            with IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True) as client:
                client.login(config["email"], config["password"])
                client.select_folder("INBOX")
                logging.info(f"Watching {config['email']}")
                while True:
                    client.idle()
                    responses = client.idle_check(timeout=60)
                    client.idle_done()
                    if responses:
                        messages = client.search("UNSEEN")
                        for uid in messages:
                            raw = client.fetch([uid], ["RFC822"])[uid][b"RFC822"]
                            msg = email.message_from_bytes(raw)
                            payload = {
                                "inbox": config["email"],
                                "from": msg.get("From"),
                                "subject": msg.get("Subject"),
                                "body": parse_body(msg),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                            send_to_n8n(payload)
                            client.set_flags([uid], ["\\Seen"])
        except Exception as e:
            logging.error(f"Error on {config['email']}: {e}. Reconnecting in 10s...")
            time.sleep(10)

if __name__ == "__main__":
    threads = []
    for inbox in INBOXES:
        t = threading.Thread(target=watch_inbox, args=(inbox,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
