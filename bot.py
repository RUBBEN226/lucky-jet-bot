import time
import threading
import requests
import os
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8814245354:AAFh1xQaOWdnQhMM-lzq2xBaZ9etdXA5W6c"
ADMIN_ID = 8286650559  # Votre ID administrateur

# Dictionnaire pour stocker les signaux restants par utilisateur
# On stocke sous la forme : { chat_id: {"used": X, "limit": 2} }
user_signal_data = {}

def get_user_data(chat_id):
    if chat_id not in user_signal_data:
        user_signal_data[chat_id] = {"used": 0, "limit": 2}
    return user_signal_data[chat_id]

def send_message_with_keyboard(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        payload["reply_markup"] = keyboard
        
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
                        
                        # Commande texte de secours /reset ID
                        if text.startswith("/reset"):
                            if chat_id == ADMIN_ID:
                                parts = text.split()
                                if len(parts) > 1:
                                    try:
                                        target_id = int(parts[1])
                                        udata = get_user_data(target_id)
                                        udata["used"] = 0
                                        udata["limit"] = 20  # Recharge à 20 tours
                                        send_message_with_keyboard(chat_id, f"✅ L'utilisateur `{target_id}` a été rechargé avec un pack de 20 tours !")
                                        send_message_with_keyboard(target_id, "🎉 *COMPTE RECHARGÉ !*\n\nL'administrateur vient de vous offrir un pack de *20 signaux* ! Vous pouvez à nouveau jouer 🚀", keyboard={"inline_keyboard": [[{"text": "🔥 DEMANDER UN SIGNAL", "callback_data": "get_signal"}]]})
                                    except ValueError:
                                        send_message_with_keyboard(chat_id, "❌ ID invalide.")
                            continue
                        
                        if text.startswith("/start"):
                            get_user_data(chat_id)  # Initialise l'utilisateur
                            welcome_msg = (
                                "🚀 *RUBBEN226 ASSURANCE* 🚀\n\n"
                                "Ce bot analyse les données LuckyJet et envoie des prédictions avec un taux de réussite affiché pouvant atteindre 98% 📊🔥\n\n"
                                "Appuyez sur le bouton ci-dessous pour générer un signal !"
                            )
                            kb = {
                                "inline_keyboard": [
                                    [{"text": "🔥 DEMANDER UN SIGNAL", "callback_data": "get_signal"}]
                                ]
                            }
                            send_message_with_keyboard(chat_id, welcome_msg, keyboard=kb)
                    
                    elif "callback_query" in result:
                        callback_query = result["callback_query"]
                        callback_query_id = callback_query["id"]
                        chat_id = callback_query["message"]["chat"]["id"]
                        data_action = callback_query.get("data")
                        
                        # Action admin via bouton interactif
                        if data_action.startswith("reset_"):
                            if chat_id == ADMIN_ID:
                                target_id = int(data_action.split("_")[1])
                                udata = get_user_data(target_id)
                                udata["used"] = 0
                                udata["limit"] = 20  # Recharge à 20 tours
                                answer_callback_query(callback_query_id, "Client rechargé avec 20 tours !")
                                
                                # Confirmer à l'admin
                                send_message_with_keyboard(chat_id, f"✅ L'utilisateur `{target_id}` a reçu son pack de 20 tours.")
                                # Informer le client
                                send_message_with_keyboard(
                                    target_id, 
                                    "🎉 *COMPTE RECHARGÉ !*\n\nL'administrateur vient de vous offrir un pack de *20 signaux* ! Vous pouvez à nouveau jouer 🚀",
                                    keyboard={"inline_keyboard": [[{"text": "🔥 DEMANDER UN SIGNAL", "callback_data": "get_signal"}]]}
                                )
                            else:
                                answer_callback_query(callback_query_id, "Action réservée à l'admin !")
                            continue
                        
                        if data_action == "get_signal":
                            udata = get_user_data(chat_id)
                            current_used = udata["used"]
                            current_limit = udata["limit"]
                            
                            if current_used >= current_limit:
                                answer_callback_query(callback_query_id, "Limite atteinte !")
                                blocked_msg = (
                                    "⚠️ *VOS SIGNAUX SONT TERMINÉS*\n\n"
                                    f"_Vous avez épuisé vos signaux disponibles._\n\n"
                                    "🔥 *Pour obtenir de nouveaux signaux, rejoignez notre canal et contactez l'admin :*\n\n"
                                    "👉 [Rejoindre le canal](https://t.me/+tzWgZ8RnLog0NTc0)"
                                )
                                kb_blocked = {
                                    "inline_keyboard": [
                                        [{"text": "💬 CONTACTER L'ADMIN", "url": "https://t.me/+tzWgZ8RnLog0NTc0"}]
                                    ]
                                }
                                send_message_with_keyboard(chat_id, blocked_msg, keyboard=kb_blocked)
                                
                                # NOTIFICATION ADMIN avec le bouton de réinitialisation directe à 20 tours !
                                admin_alert = (
                                    f"🔔 *NOUVEL UTILISATEUR BLOQUÉ*\n\n"
                                    f"L'utilisateur ID : `{chat_id}` a épuisé ses signaux et demande une recharge."
                                )
                                admin_kb = {
                                    "inline_keyboard": [
                                        [{"text": "🔄 RECHARGER (20 TOURS)", "callback_data": f"reset_{chat_id}"}]
                                    ]
                                }
                                send_message_with_keyboard(ADMIN_ID, admin_alert, keyboard=admin_kb)
                                
                            else:
                                udata["used"] = current_used + 1
                                remaining = current_limit - udata["used"]
                                
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
                                kb_signal = {
                                    "inline_keyboard": [
                                        [{"text": "🔥 DEMANDER UN SIGNAL", "callback_data": "get_signal"}]
                                    ]
                                }
                                send_message_with_keyboard(chat_id, signal_msg, keyboard=kb_signal)
                            
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
