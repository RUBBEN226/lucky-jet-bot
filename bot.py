import time
import threading
import requests
import os
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8814245354:AAFh1xQaOWdnQhMM-lzq2xBaZ9etdXA5W6c"
ADMIN_ID = 8286650559  # Votre ID administrateur

user_signal_data = {}

def get_user_data(chat_id):
    if chat_id not in user_signal_data:
        user_signal_data[chat_id] = {"used": 0, "limit": 2, "waiting_deposit": False, "last_signal_time": None}
    return user_signal_data[chat_id]

# Clavier persistant du bas (Menu)
MAIN_MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "⚡ Obtenir un Signal ⚡"}, {"text": "📸 Envoyer mon ID 1Win"}],
        [{"text": "📖 Guide Inscription (RUBB225)"}, {"text": "🆔 Mon ID Telegram"}],
        [{"text": "🎁 Code Promo : RUBB225"}, {"text": "💬 Contacter l'Admin"}],
        [{"text": "🔄 Vérifier mon Accès"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

def send_message_with_menu(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": MAIN_MENU_KEYBOARD
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
                    
                    if "message" in result:
                        msg = result["message"]
                        chat_id = msg["chat"]["id"]
                        
                        # Gestion des preuves de dépôt / ID
                        if chat_id != ADMIN_ID:
                            udata = get_user_data(chat_id)
                            if udata.get("waiting_deposit"):
                                forward_url = f"https://api.telegram.org/bot{TOKEN}/forwardMessage"
                                requests.post(forward_url, json={
                                    "chat_id": ADMIN_ID,
                                    "from_chat_id": chat_id,
                                    "message_id": msg["message_id"]
                                })
                                
                                admin_alert = (
                                    f"📥 *PREUVE DE DÉPÔT / ID REÇUE*\n\n"
                                    f"De l'utilisateur ID : `{chat_id}`\n"
                                    "Vérifiez l'ID ci-dessus sur votre tableau de bord partenaire, puis validez :"
                                )
                                admin_kb = {
                                    "inline_keyboard": [
                                        [{"text": "✅ VALIDER ET OFFRIR 50 TOURS", "callback_data": f"reset_{chat_id}"}],
                                        [{"text": "❌ REJETER", "callback_data": f"reject_{chat_id}"}]
                                    ]
                                }
                                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                                    "chat_id": ADMIN_ID,
                                    "text": admin_alert,
                                    "parse_mode": "Markdown",
                                    "reply_markup": admin_kb
                                })
                                
                                send_message_with_menu(chat_id, "⏳ *ID / Preuve bien reçu !*\n\nL'administrateur va vérifier votre inscription avec le code promo **RUBB225** et rechargera votre compte avec 50 signaux sous peu.")
                                udata["waiting_deposit"] = False
                                continue

                        if "text" in msg:
                            text = msg["text"].strip()
                            udata = get_user_data(chat_id)
                            
                            if text.startswith("/start"):
                                welcome_msg = (
                                    "🚀 *RUBBEN226 ASSURANCE* 🚀\n\n"
                                    "Bienvenue ! Utilisez les boutons du menu en bas pour naviguer, obtenir vos signaux ou valider votre accès :"
                                )
                                send_message_with_menu(chat_id, welcome_msg)
                                continue
                                
                            elif text == "⚡ Obtenir un Signal ⚡":
                                now = datetime.now()
                                if udata["last_signal_time"] is None or udata["last_signal_time"] < now:
                                    base_time = now + timedelta(minutes=1)
                                else:
                                    add_mins = random.randint(1, 2)
                                    base_time = udata["last_signal_time"] + timedelta(minutes=add_mins)
                                
                                udata["last_signal_time"] = base_time
                                future_time = base_time.strftime("%H:%M")
                                
                                if chat_id == ADMIN_ID:
                                    coeff = round(random.uniform(1.50, 4.50), 2)
                                    assurance = round(coeff * 0.9, 2)
                                    success_rate = random.randint(93, 98)
                                    
                                    signal_msg = (
                                        "👑 *MODE ADMINISTRATEUR (ILLIMITÉ)* 👑\n\n"
                                        f"🔥 *SIGNAL* 🔥\n"
                                        f"🚀 *COEFFICIENT* – {coeff}X+\n"
                                        f"🛡️ *ASSURANCE* – {assurance}X\n"
                                        f"📊 *TAUX DE RÉUSSITE* – {success_rate}%\n"
                                        f"⏱️ *HEURE DE JEU* – {future_time}±"
                                    )
                                    send_message_with_menu(chat_id, signal_msg)
                                    continue

                                current_used = udata["used"]
                                current_limit = udata["limit"]
                                
                                if current_used >= current_limit:
                                    blocked_msg = (
                                        "⚠️ *VOS SIGNAUX SONT TERMINÉS*\n\n"
                                        "_Vous avez épuisé vos signaux disponibles._\n\n"
                                        "🔥 *Pour activer votre robot 100% LuckyJet et obtenir 50 nouveaux signaux :*\n"
                                        "1. Inscrivez-vous avec le code promo *RUBB225*\n"
                                        "2. Faites votre dépôt\n"
                                        "3. Cliquez sur 'Envoyer mon ID 1Win' ci-dessous !"
                                    )
                                    send_message_with_menu(chat_id, blocked_msg)
                                else:
                                    udata["used"] = current_used + 1
                                    remaining = current_limit - udata["used"]
                                    
                                    coeff = round(random.uniform(1.50, 4.50), 2)
                                    assurance = round(coeff * 0.9, 2)
                                    success_rate = random.randint(93, 98)
                                    
                                    signal_msg = (
                                        "🔥 *SIGNAL PREMIUM* 🔥\n\n"
                                        f"🚀 *COEFFICIENT* – {coeff}X+\n"
                                        f"🛡️ *ASSURANCE* – {assurance}X\n"
                                        f"📊 *TAUX DE RÉUSSITE* – {success_rate}%\n"
                                        f"⏱️ *HEURE DE JEU* – {future_time}±\n\n"
                                        f"📊 *Signaux restants* : {remaining}\n\n"
                                        "Inscrivez-vous avec le code promo *RUBB225* :\n"
                                        "👉 [Lien d'inscription](https://1win.ci/casino?p=4kpi)"
                                    )
                                    send_message_with_menu(chat_id, signal_msg)
                                continue
                                
                            elif text == "📸 Envoyer mon ID 1Win":
                                udata["waiting_deposit"] = True
                                send_message_with_menu(chat_id, "📸 *ENVOYEZ VOTRE ID 1WIN*\n\nVeuillez envoyer maintenant une **capture d'écran de votre ID 1win** dans cette conversation.")
                                continue
                                
                            elif text == "📖 Guide Inscription (RUBB225)":
                                guide_msg = (
                                    "📖 *GUIDE D'INSCRIPTION & ACTIVATION* 📖\n\n"
                                    "1️⃣ Créez un compte sur 1Win en utilisant le code promo : `RUBB225`\n"
                                    "2️⃣ Effectuez votre premier dépôt.\n"
                                    "3️⃣ Cliquez sur **Envoyer mon ID 1Win** pour nous transmettre votre capture d'écran.\n"
                                    "4️⃣ Recevez vos **50 signaux** après validation par l'administrateur !"
                                )
                                send_message_with_menu(chat_id, guide_msg)
                                continue
                                
                            elif text == "🆔 Mon ID Telegram":
                                send_message_with_menu(chat_id, f"🆔 Votre identifiant Telegram est : `{chat_id}`")
                                continue
                                
                            elif text == "🎁 Code Promo : RUBB225":
                                send_message_with_menu(chat_id, "🎁 *CODE PROMO OFFICIEL* :\n\nUtilisez le code `RUBB225` lors de votre inscription sur 1Win pour débloquer votre accès au robot.")
                                continue
                                
                            elif text == "💬 Contacter l'Admin":
                                send_message_with_menu(chat_id, "💬 Pour contacter directement l'administrateur, écrivez ici : https://t.me/+tzWgZ8RnLog0NTc0")
                                continue
                                
                            elif text == "🔄 Vérifier mon Accès":
                                used = udata["used"]
                                limit = udata["limit"]
                                remaining = max(0, limit - used)
                                status_msg = (
                                    "📊 *STATUT DE VOTRE COMPTE*\n\n"
                                    f"• Signaux utilisés : {used}/{limit}\n"
                                    f"• Signaux restants : {remaining}\n"
                                    f"• Mode : {'Administrateur 👑' if chat_id == ADMIN_ID else 'Membre Standard'}"
                                )
                                send_message_with_menu(chat_id, status_msg)
                                continue
                    
                    elif "callback_query" in result:
                        callback_query = result["callback_query"]
                        callback_query_id = callback_query["id"]
                        chat_id = callback_query["message"]["chat"]["id"]
                        data_action = callback_query.get("data")
                        
                        if data_action.startswith("reset_"):
                            if chat_id == ADMIN_ID:
                                target_id = int(data_action.split("_")[1])
                                udata = get_user_data(target_id)
                                udata["used"] = 0
                                udata["limit"] = 50
                                udata["last_signal_time"] = None
                                answer_callback_query(callback_query_id, "Client rechargé avec 50 tours !")
                                
                                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                                    "chat_id": ADMIN_ID,
                                    "text": f"✅ L'utilisateur `{target_id}` a reçu son pack de 50 tours.",
                                    "parse_mode": "Markdown"
                                })
                                send_message_with_menu(
                                    target_id, 
                                    "🎉 *ACTIVATION VALIDÉE & COMPTE RECHARGÉ !*\n\nL'administrateur a validé votre ID 1win. Vous avez reçu un pack de *50 signaux* ! Vous pouvez jouer 🚀"
                                )
                            else:
                                answer_callback_query(callback_query_id, "Action réservée à l'admin !")
                            continue
                            
                        if data_action.startswith("reject_"):
                            if chat_id == ADMIN_ID:
                                target_id = int(data_action.split("_")[1])
                                answer_callback_query(callback_query_id, "Rejeté.")
                                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                                    "chat_id": ADMIN_ID,
                                    "text": f"❌ Demande de l'utilisateur `{target_id}` rejetée.",
                                    "parse_mode": "Markdown"
                                })
                                send_message_with_menu(target_id, "❌ *Vérification échouée*\n\nL'ID ou le dépôt n'a pas pu être validé avec le code promo *RUBB225*. Veuillez réessayer.")
                            continue
                            
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
