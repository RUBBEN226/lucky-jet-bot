
import time
import threading
import requests
import os
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8814245354:AAFh1xQaOWdnQhMM-lzq2xBaZ9etdXA5W6c"

# Dictionnaire pour compter les signaux par utilisateur
user_signal_counts = {}
MAX_FREE_SIGNALS = 2

def send_message_with_keyboard(chat_id, text, is_blocked=False):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    if is_blocked:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💬 CONTACTER L'ADMIN", "url": "https://t.me/+tzWgZ8RnLog0NTc0"}]
            ]
        }
    else:
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
                            if chat_id not in user_signal_counts:
                                user_signal_counts[chat_id] = 0
                                
                            welcome_msg = (
                                "🚀 *RUBBEN226 ASSURANCE* 🚀\n\n"
                                "Ce bot analyse les données LuckyJet et envoie des prédictions avec un taux de réussite affiché pouvant atteindre 98% 📊🔥\n\n"
                                "Appuyez sur le bouton ci-dessous pour générer un signal !"
                            )
                            send_message_with_keyboard(chat_id, welcome_msg, is_blocked=False)
                    
                    elif "callback_query" in result:
                        callback_query = result["callback_query"]
                        callback_query_id = callback_query["id"]
                        chat_id = callback_query["message"]["chat"]["id"]
                        data_action = callback_query.get("data")
                        
                        if data_action == "get_signal":
                            current_count = user_signal_counts.get(chat_id, 0)
                            
                            if current_count >= MAX_FREE_SIGNALS:
                                answer_callback_query(callback_query_id, "Limite atteinte !")
                                blocked_msg = (
                                    "⚠️ *VOS SIGNAUX SONT TERMINÉS*\n\n"
                                    f"_Vous avez utilisé vos {MAX_FREE_SIGNALS} signaux gratuits._\n\n"
                                    "🔥 *Pour obtenir de nouveaux signaux, contactez l'administrateur :*\n\n"
                                    "👉 [Cliquez ici pour contacter l'admin](https://t.me/+tzWgZ8RnLog0NTc0)"
                                )
                                send_message_with_keyboard(chat_id, blocked_msg, is_blocked=True)
                            else:
                                user_signal_counts[chat_id] = current_count + 1
                                remaining = MAX_FREE_SIGNALS - user_signal_counts[chat_id]
                                
                                answer_callback_query(callback_query_id, f"Signal généré ! ({remaining} restants)")
                                
                                coeff = round(random.uniform(1.50, 4.50), 2)
                                assurance = round(coeff * 0.9, 2)
                                success_rate = random.randint(93, 98)
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
                                send_message_with_keyboard(chat_id, signal_msg, is_blocked=False)
                            
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
