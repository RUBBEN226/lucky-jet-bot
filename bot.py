import time
import threading
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8814245354:AAFh1xQaOWdnQhMM-lzq2xBaZ9etdXA5W6c"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erreur d'envoi :", e)

def listen_telegram_updates():
    offset = 0
    print("Démarrage de l'écoute des messages Telegram...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    
                    if "message" in result and "text" in result["message"]:
                        chat_id = result["message"]["chat"]["id"]
                        text = result["message"]["text"].strip()
                        
                        if text.startswith("/start"):
                            welcome_msg = (
                                "🚀 *Bienvenue sur le bot Lucky Jet & 1win* 🚀\n\n"
                                "Restez concentrés, gérez votre capital et ne cédez pas à la panique avec vos émotions !\n\n"
                                "Inscrivez-vous dès maintenant sur 1win et profitez de vos avantages avec le code promo : *RUBB225*\n"
                                "👉 [Cliquez ici pour vous inscrire](https://1win.ci/casino?p=4kpi)"
                            )
                            send_message(chat_id, welcome_msg)
                            
        except Exception as e:
            print("Erreur dans la boucle d'écoute :", e)
            time.sleep(5)

threading.Thread(target=listen_telegram_updates, daemon=True).start()

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
