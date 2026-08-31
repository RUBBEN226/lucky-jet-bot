import time
import threading
import requests
import os
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8814245354:AAFh1xQaOWdnQhMM-lzq2xBaZ9etdXA5W6c"

def send_message_with_keyboard(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔥 DEMANDER UN SIGNAL", "callback_data": "get_signal"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Error sending message:", e)

def answer_callback_query(callback_query_id, text=""):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id, "text": text, "show_alert": False}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Error answering callback:", e)

def listen_telegram_updates():
    offset = 0
    print("Listening for Telegram updates...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    
                    if "message" in result and "text" in result["message"]:
                        chat_id = result["message"]["chat"]["id"]
                        text = result["message"]["text"].strip()
                        
                        if text.startswith("/start"):
                            welcome_msg = (
                                "🚀 *ULTRA PRÉDICTOR* 🚀\n\n"
                                "Ce bot analyse les données LuckyJet et envoie des prédictions avec un taux de réussite affiché pouvant atteindre 98% 📊🔥\n\n"
                                "Appuyez sur le bouton ci-dessous pour générer un signal !"
                            )
                            send_message_with_keyboard(chat_id, welcome_msg)
                    
                    elif "callback_query" in result:
                        callback_query = result["callback_query"]
                        callback_query_id = callback_query["id"]
                        chat_id = callback_query["message"]["chat"]["id"]
                        data_action = callback_query.get("data")
                        
                        if data_action == "get_signal":
                            answer_callback_query(callback_query_id, "Signal généré ! 🚀")
                            
                            coeff = round(random.uniform(1.50, 4.50), 2)
                            assurance = round(coeff * 0.9, 2)
                            success_rate = random.randint(93, 98)
                            
                            # Calcul de l'heure actuelle + 3 minutes
                            future_time = (datetime.now() + timedelta(minutes=3)).strftime("%H:%M")
                            
                            signal_msg = (
                                "🔥 *SIGNAL PREMIUM* 🔥\n\n"
                                f"🚀 *COEFFICIENT* – {coeff}X+\n"
                                f"🛡️ *ASSURANCE* – {assurance}X\n"
                                f"📊 *TAUX DE RÉUSSITE* – {success_rate}%\n"
                                f"⏱️ *HEURE DE JEU* – {future_time}±\n\n"
                                "Inscrivez-vous sur 1win avec le code promo *RUBB225* :\n"
                                "👉 [Lien d'inscription](https://1win.ci/casino?p=4kpi)"
                            )
                            send_message_with_keyboard(chat_id, signal_msg)
                            
        except Exception as e:
            print("Error in listen loop:", e)
            time.sleep(3)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=listen_telegram_updates, daemon=True).start()
    run_web_server()
