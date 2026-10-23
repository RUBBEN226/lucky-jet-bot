

import os
import random
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8286650559
REGISTER_URL = "https://1win.ci/casino?p=4kpi"
PROMO_CODE = "RUBB225"

if not TOKEN:
    raise RuntimeError("Configure BOT_TOKEN dans les variables Render.")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_signal_data = {}


def get_user_data(chat_id):
    if chat_id not in user_signal_data:
        user_signal_data[chat_id] = {
            "used": 0,
            "limit": 999999 if chat_id == ADMIN_ID else 2,
            "waiting_deposit": False,
            "last_signal_time": None
        }
    return user_signal_data[chat_id]


MAIN_MENU_KEYBOARD = {
    "keyboard": [
        [
            {"text": "⚡ Obtenir un Signal ⚡"},
            {"text": "📸 Envoyer mon ID 1Win"}
        ],
        [
            {"text": "📖 Guide Inscription (RUBB225)"},
            {"text": "🆔 Mon ID Telegram"}
        ],
        [
            {"text": "🎁 Code Promo : RUBB225"},
            {"text": "💬 Contacter l'Admin"}
        ],
        [{"text": "🔄 Vérifier mon Accès"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}


def telegram(method, payload):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/{method}",
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            logging.error("Erreur Telegram : %s", result)

        return result

    except requests.RequestException:
        logging.exception("Erreur API Telegram")
        return {"ok": False}


def send_message_with_menu(chat_id, text, keyboard=None):
    return telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard or MAIN_MENU_KEYBOARD
    })


def answer_callback_query(callback_id, text=""):
    return telegram("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": text,
        "show_alert": True
    })


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    try:
        # Validation des boutons administrateur
        if "callback_query" in data:
            cq = data["callback_query"]
            callback_id = cq["id"]
            admin_chat_id = cq.get("message", {}).get(
                "chat", {}
            ).get("id")
            action = cq.get("data", "")

            if admin_chat_id != ADMIN_ID:
                answer_callback_query(
                    callback_id,
                    "Action réservée à l'administrateur."
                )
                return "OK", 200

            if action.startswith("reset_"):
                try:
                    target_id = int(action.split("_", 1)[1])
                except (ValueError, IndexError):
                    answer_callback_query(
                        callback_id, "Identifiant invalide."
                    )
                    return "OK", 200

                udata = get_user_data(target_id)

                # Ajouter 50 signaux au solde existant
                udata["limit"] += 50

                remaining = max(0, udata["limit"] - udata["used"])
                result = send_message_with_menu(
                    target_id,
                    "🎉 *ACCÈS RECHARGÉ !*\n\n"
                    "Votre demande a été validée par "
                    "l'administrateur.\n"
                    "✅ *50 signaux supplémentaires ont été ajoutés.*\n\n"
                    f"📊 Signaux disponibles : {remaining}\n\n"
                    "⚠️ Les signaux sont indicatifs et ne garantissent "
                    "aucun gain. Jouez de manière responsable."
                )

                if result.get("ok"):
                    answer_callback_query(
                        callback_id,
                        "Succès : 50 signaux ajoutés au client."
                    )
                    telegram("sendMessage", {
                        "chat_id": ADMIN_ID,
                        "text": (
                            "✅ Validation effectuée.\n"
                            f"Client : {target_id}\n"
                            "50 signaux supplémentaires ajoutés."
                        )
                    })
                else:
                    # Annuler l'ajout si le message au client échoue
                    udata["limit"] -= 50
                    answer_callback_query(
                        callback_id,
                        "Échec de l'envoi au client. Vérifiez son accès."
                    )

            elif action.startswith("reject_"):
                try:
                    target_id = int(action.split("_", 1)[1])
                except (ValueError, IndexError):
                    answer_callback_query(
                        callback_id, "Identifiant invalide."
                    )
                    return "OK", 200

                get_user_data(target_id)["waiting_deposit"] = False
                answer_callback_query(callback_id, "Demande rejetée.")

                send_message_with_menu(
                    target_id,
                    "❌ *Demande non validée*\n\n"
                    "Votre demande n'a pas été validée. "
                    "Veuillez contacter l'administrateur."
                )

            else:
                answer_callback_query(callback_id, "Action inconnue.")

            return "OK", 200

        # Traitement des messages
        if "message" not in data:
            return "OK", 200

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        udata = get_user_data(chat_id)
        text = msg.get("text", "").strip()

        # Réception de l'ID ou d'une capture d'écran
        if chat_id != ADMIN_ID and udata["waiting_deposit"]:
            forwarded = telegram("forwardMessage", {
                "chat_id": ADMIN_ID,
                "from_chat_id": chat_id,
                "message_id": msg["message_id"]
            })

            if forwarded.get("ok"):
                admin_keyboard = {
                    "inline_keyboard": [
                        [{
                            "text": "✅ VALIDER ET OFFRIR 50 TOURS",
                            "callback_data": f"reset_{chat_id}"
                        }],
                        [{
                            "text": "❌ REJETER",
                            "callback_data": f"reject_{chat_id}"
                        }]
                    ]
                }

                telegram("sendMessage", {
                    "chat_id": ADMIN_ID,
                    "text": (
                        "📥 *ID / PREUVE REÇUE*\n\n"
                        f"Identifiant Telegram : `{chat_id}`\n"
                        "Vérifiez les informations avant de décider."
                    ),
                    "parse_mode": "Markdown",
                    "reply_markup": admin_keyboard
                })

                send_message_with_menu(
                    chat_id,
                    "⏳ Votre demande a été transmise "
                    "à l'administrateur pour vérification."
                )
                udata["waiting_deposit"] = False
            else:
                send_message_with_menu(
                    chat_id,
                    "❌ Impossible de transmettre votre message. "
                    "Veuillez réessayer."
                )

            return "OK", 200

        if not text:
            return "OK", 200

        # Démarrage
        if text.startswith("/start"):
            send_message_with_menu(
                chat_id,
                "🚀 *RUBBEN226 ASSURANCE* 🚀\n\n"
                "Bienvenue ! Utilisez les boutons ci-dessous "
                "pour naviguer.\n\n"
                "⚠️ Les jeux comportent un risque de perte. "
                "Aucun signal ne garantit un gain."
            )

        # Demande de signal
        elif text == "⚡ Obtenir un Signal ⚡":
            if chat_id != ADMIN_ID and udata["used"] >= udata["limit"]:
                send_message_with_menu(
                    chat_id,
                    "⚠️ *VOS SIGNAUX SONT TERMINÉS*\n\n"
                    "Vous pouvez envoyer votre ID pour demander "
                    "une vérification d'accès.\n\n"
                    "Les signaux ne garantissent aucun gain."
                )
                return "OK", 200

            now = datetime.now()
            last = udata["last_signal_time"]

            if last is None or last < now:
                signal_time = now + timedelta(minutes=1)
            else:
                signal_time = last + timedelta(
                    minutes=random.randint(1, 2)
                )

            udata["last_signal_time"] = signal_time
            future_time = signal_time.strftime("%H:%M")

            coeff = round(random.uniform(1.50, 4.50), 2)
            assurance = round(coeff * 0.90, 2)

            if chat_id != ADMIN_ID:
                udata["used"] += 1

            signal_msg = (
                "🔥 *SIGNAL INDICATIF* 🔥\n\n"
                f"🚀 Coefficient : {coeff}X\n"
                f"🛡️ Niveau indicatif : {assurance}X\n"
                f"⏰ Heure indicative : {future_time}\n\n"
                "⚠️ Ces valeurs sont générées aléatoirement. "
                "Elles ne prédisent pas les résultats du jeu "
                "et ne garantissent aucun gain."
            )

            if chat_id == ADMIN_ID:
                signal_msg = "👑 *MODE ADMINISTRATEUR*\n\n" + signal_msg
            else:
                signal_msg += (
                    f"\n\n📊 Signaux restants : "
                    f"{max(0, udata['limit'] - udata['used'])}"
                )

            send_message_with_menu(chat_id, signal_msg)

        # Envoyer son ID
        elif text == "📸 Envoyer mon ID 1Win":
            udata["waiting_deposit"] = True
            send_message_with_menu(
                chat_id,
                "📸 *ENVOYEZ VOTRE ID 1WIN*\n\n"
                "Envoyez votre identifiant ou une capture "
                "d'écran dans cette conversation."
            )

        # Guide d'inscription avec le lien fourni
        elif text == "📖 Guide Inscription (RUBB225)":
            send_message_with_menu(
                chat_id,
                "📖 *GUIDE D'INSCRIPTION*\n\n"
                "1️⃣ Accédez au site via ce lien :\n"
                f"{REGISTER_URL}\n\n"
                "2️⃣ Suivez les instructions d'inscription.\n"
                f"3️⃣ Code promo : *{PROMO_CODE}*\n\n"
                "4️⃣ Lisez les conditions du bonus, de dépôt "
                "et de retrait avant toute transaction.\n\n"
                "⚠️ Réservé aux personnes majeures. "
                "Jouez avec responsabilité : un dépôt ne garantit "
                "aucun gain. Ne misez que de l'argent que vous "
                "pouvez vous permettre de perdre."
            )

        # Identifiant Telegram
        elif text == "🆔 Mon ID Telegram":
            send_message_with_menu(
                chat_id,
                f"🆔 Votre identifiant Telegram est : `{chat_id}`"
            )

        # Code promo et message de prudence
        elif text == "🎁 Code Promo : RUBB225":
            send_message_with_menu(
                chat_id,
                "🎁 *CODE PROMO : RUBB225*\n\n"
                f"🔗 Lien d'inscription :\n{REGISTER_URL}\n\n"
                "Si vous choisissez de vous inscrire, vérifiez "
                "les conditions d'utilisation du code promo.\n\n"
                "💡 Avant tout dépôt, assurez-vous de comprendre "
                "les conditions de l'offre et de disposer "
                "d'un budget adapté.\n\n"
                "⚠️ Jouez de manière responsable. Un dépôt ne "
                "garantit aucun gain. Ne déposez jamais l'argent "
                "nécessaire à vos dépenses essentielles et "
                "n'essayez pas de récupérer vos pertes."
            )

        # Contacter l'administrateur
        elif text == "💬 Contacter l'Admin":
            send_message_with_menu(
                chat_id,
                "💬 Contact administrateur :\n"
                "https://t.me/+tzWgZ8RnLog0NTc0"
            )

        # Vérifier son accès
        elif text == "🔄 Vérifier mon Accès":
            if chat_id == ADMIN_ID:
                status_msg = (
                    "📊 *STATUT ADMINISTRATEUR*\n\n"
                    "Accès administrateur activé."
                )
            else:
                used = udata["used"]
                limit = udata["limit"]
                status_msg = (
                    "📊 *STATUT DE VOTRE COMPTE*\n\n"
                    f"• Signaux utilisés : {used}/{limit}\n"
                    f"• Signaux restants : {max(0, limit - used)}"
                )

            send_message_with_menu(chat_id, status_msg)

    except Exception:
        logging.exception("Erreur de traitement du webhook")

    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    return "Bot Telegram actif", 200


if __name__ == "__main__":
    render_url = os.environ.get("RENDER_EXTERNAL_URL")

    if render_url:
        webhook_url = f"{render_url.rstrip('/')}/{TOKEN}"
        result = telegram("setWebhook", {"url": webhook_url})
        logging.info("Configuration webhook : %s", result)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
