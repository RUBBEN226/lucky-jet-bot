

import os
import random
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8286650559

REGISTER_URL = "https://1win.ci/casino?p=4kpi"
PROMO_CODE = "RUBB225"

if not TOKEN:
    raise RuntimeError(
        "Configure BOT_TOKEN dans les variables d'environnement Render."
    )

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# DONNEES DES UTILISATEURS
# Attention : stockage en mémoire
# =========================
user_signal_data = {}
pending_users = {}


def get_user_data(user_id):
    if user_id not in user_signal_data:
        user_signal_data[user_id] = {
            "used": 0,
            "limit": 2,
            "last_signal_time": None,
            "waiting_id": False,
            "waiting_proof": False,
            "win_id": None,
            "approved": False,
        }
    return user_signal_data[user_id]


# =========================
# FONCTIONS TELEGRAM
# =========================
def telegram(method, payload=None, files=None):
    try:
        response = requests.post(
            f"{API_URL}/{method}",
            data=payload,
            files=files,
            timeout=30,
        )
        result = response.json()

        if not result.get("ok"):
            logger.error("Erreur Telegram : %s", result)

        return result

    except requests.RequestException as exc:
        logger.error("Erreur réseau Telegram : %s", exc)
        return {"ok": False}


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        import json
        payload["reply_markup"] = json.dumps(reply_markup)

    return telegram("sendMessage", payload)


def answer_callback(callback_id, text):
    return telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id,
            "text": text,
        },
    )


def main_menu():
    return {
        "keyboard": [
            [
                {"text": "🎯 Obtenir un signal"},
                {"text": "🆔 Envoyer mon ID 1Win"},
            ],
            [
                {"text": "📘 Guide d'inscription"},
                {"text": "🆔 Mon ID Telegram"},
            ],
            [
                {"text": "🎁 Code promo"},
                {"text": "🔎 Vérifier mon accès"},
            ],
            [
                {"text": "📞 Contact de l'admin"},
            ],
        ],
        "resize_keyboard": True,
    }


def admin_buttons(user_id):
    return {
        "inline_keyboard": [
            [
                {
                    "text": "✅ VALIDER ET OFFRIR 50 TOURS",
                    "callback_data": f"approve_{user_id}",
                }
            ],
            [
                {
                    "text": "❌ REJETER",
                    "callback_data": f"reject_{user_id}",
                }
            ],
        ]
    }


# =========================
# DEMARRAGE
# =========================
def start_command(chat_id, user_id, first_name="ami"):
    get_user_data(user_id)

    send_message(
        chat_id,
        f"👋 Bienvenue {first_name} sur RUBBEN226 ASSISTANT !\n\n"
        "Voici les services disponibles :\n\n"
        "🎯 Obtenir un signal\n"
        "🆔 Envoyer ton ID 1Win\n"
        "📘 Guide d'inscription\n"
        "🆔 Consulter ton ID Telegram\n"
        "🎁 Code promo\n"
        "🔎 Vérifier ton accès\n"
        "📞 Contacter l'administrateur\n\n"
        "⚠️ Les signaux sont indicatifs et ne garantissent "
        "aucun gain. Joue de manière responsable.",
        main_menu(),
    )


# =========================
# ENVOI D'UNE DEMANDE A L'ADMIN
# =========================
def submit_for_review(user_id, chat_id, description):
    data = get_user_data(user_id)

    pending_users[user_id] = {
        "chat_id": chat_id,
        "win_id": data.get("win_id"),
        "submitted_at": datetime.utcnow().isoformat(),
    }

    message = (
        "📥 NOUVELLE DEMANDE DE VALIDATION\n\n"
        f"👤 Nom/ID Telegram : {user_id}\n"
        f"🆔 ID 1Win : {data.get('win_id') or 'Non fourni'}\n"
        f"📄 Preuve : {description}\n\n"
        "Vérifie les informations avant de décider."
    )

    send_message(
        ADMIN_ID,
        message,
        admin_buttons(user_id),
    )

    send_message(
        chat_id,
        "✅ Ta demande a été transmise à l'administrateur.\n\n"
        "⏳ Attends la vérification. Tu recevras un message "
        "lorsque la décision sera prise.",
        main_menu(),
    )


# =========================
# TRAITEMENT DES MESSAGES
# =========================
def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()
    data = get_user_data(user_id)

    first_name = message.get("from", {}).get("first_name", "ami")

    if text.startswith("/start"):
        start_command(chat_id, user_id, first_name)
        return

    if text == "🆔 Mon ID Telegram":
        send_message(
            chat_id,
            f"🆔 Ton identifiant Telegram est : {user_id}\n\n"
            "Copie cet identifiant si l'administrateur te le demande.",
            main_menu(),
        )
        return

    if text == "📘 Guide d'inscription":
        send_message(
            chat_id,
            "📘 GUIDE D'INSCRIPTION\n\n"
            "1. Ouvre le lien d'inscription :\n"
            f"{REGISTER_URL}\n\n"
            "2. Crée ton compte en suivant les instructions "
            "officielles de la plateforme.\n\n"
            f"3. Si tu souhaites utiliser le code promo, saisis : "
            f"{PROMO_CODE}\n\n"
            "4. Si une vérification est nécessaire, envoie ton ID "
            "1Win et la preuve demandée à l'administrateur.\n\n"
            "⚠️ Vérifie les conditions du bonus. Ne dépose pas "
            "d'argent que tu ne peux pas te permettre de perdre. "
            "Un dépôt n'est pas nécessaire pour obtenir une promesse "
            "de gain et les signaux ne garantissent aucun résultat.",
            main_menu(),
        )
        return

    if text == "🎁 Code promo":
        send_message(
            chat_id,
            f"🎁 CODE PROMO : {PROMO_CODE}\n\n"
            "Lien d'inscription :\n"
            f"{REGISTER_URL}\n\n"
            "Vérifie les conditions d'utilisation du code sur "
            "la plateforme. Joue uniquement avec un budget "
            "que tu peux te permettre de perdre.",
            main_menu(),
        )
        return

    if text == "📞 Contact de l'admin":
        send_message(
            chat_id,
            f"📞 Pour contacter l'administrateur, envoie-lui "
            f"ton ID Telegram : {user_id}\n\n"
            "L'administrateur pourra ensuite te répondre "
            "sur Telegram.",
            main_menu(),
        )
        return

    if text == "🔎 Vérifier mon accès":
        remaining = max(0, data["limit"] - data["used"])
        status = (
            "✅ Accès validé"
            if data["approved"]
            else "⏳ Validation administrateur non effectuée"
        )

        send_message(
            chat_id,
            f"🔎 ÉTAT DE TON ACCÈS\n\n"
            f"Statut : {status}\n"
            f"Signaux utilisés : {data['used']}\n"
            f"Signaux disponibles : {remaining}",
            main_menu(),
        )
        return

    if text == "🆔 Envoyer mon ID 1Win":
        data["waiting_id"] = True
        send_message(
            chat_id,
            "🆔 Envoie maintenant ton identifiant 1Win "
            "dans un message texte.\n\n"
            "Vérifie bien le numéro avant de l'envoyer.",
            main_menu(),
        )
        return

    if data["waiting_id"] and text:
        data["win_id"] = text
        data["waiting_id"] = False
        data["waiting_proof"] = True

        send_message(
            chat_id,
            "✅ ID reçu.\n\n"
            "Envoie maintenant la capture d'écran de ta preuve "
            "pour que l'administrateur puisse vérifier ta demande.",
            main_menu(),
        )
        return

    if text == "🎯 Obtenir un signal":
        remaining = data["limit"] - data["used"]

        if remaining <= 0:
            send_message(
                chat_id,
                "⛔ Tu n'as plus de signaux disponibles.\n\n"
                "Pour demander une vérification, envoie ton ID 1Win "
                "et ta preuve à l'administrateur. Toute validation "
                "reste soumise à une vérification réelle.",
                main_menu(),
            )
            return

        # Exemple de signal indicatif.
        # Remplace cette partie par ta logique de signal réelle.
        multiplier = round(random.uniform(1.20, 3.00), 2)
        data["used"] += 1
        data["last_signal_time"] = datetime.utcnow().isoformat()

        send_message(
            chat_id,
            "🎯 SIGNAL INDICATIF\n\n"
            f"📊 Multiplicateur indicatif : x{multiplier}\n"
            f"🎟️ Signaux restants : {data['limit'] - data['used']}\n\n"
            "⚠️ Ce nombre est généré aléatoirement. Il ne prédit "
            "pas le résultat d'un jeu et ne garantit aucun gain.",
            main_menu(),
        )

        if data["used"] == 2 and not data["approved"]:
            send_message(
                chat_id,
                "ℹ️ Tu as utilisé tes 2 signaux initiaux.\n\n"
                "Pour demander un accès supplémentaire, consulte "
                "le guide d'inscription, puis envoie ton ID 1Win "
                "et ta preuve à l'administrateur.",
                main_menu(),
            )
        return

    # Réception d'une preuve sous forme de photo
    if message.get("photo") and data["waiting_proof"]:
        photo_id = message["photo"][-1]["file_id"]
        caption = (
            "📥 PREUVE REÇUE\n"
            f"ID Telegram : {user_id}\n"
            f"ID 1Win : {data.get('win_id') or 'Non fourni'}\n"
            "Vérifie la capture avant de décider."
        )

        result = telegram(
            "sendPhoto",
            {
                "chat_id": ADMIN_ID,
                "photo": photo_id,
                "caption": caption,
                "reply_markup": __import__("json").dumps(
                    admin_buttons(user_id)
                ),
            },
        )

        if result.get("ok"):
            data["waiting_proof"] = False
            pending_users[user_id] = {
                "chat_id": chat_id,
                "win_id": data.get("win_id"),
                "submitted_at": datetime.utcnow().isoformat(),
            }
            send_message(
                chat_id,
                "✅ Capture transmise à l'administrateur. "
                "Attends sa décision.",
                main_menu(),
            )
        else:
            send_message(
                chat_id,
                "❌ Impossible de transmettre la capture. "
                "Réessaie dans quelques instants.",
                main_menu(),
            )
        return

    if text and data["waiting_proof"]:
        submit_for_review(user_id, chat_id, text)
        data["waiting_proof"] = False
        return

    # Accepter également une demande textuelle de vérification
    if text and text.startswith("/"):
        send_message(
            chat_id,
            "Commande non reconnue. Utilise les boutons du menu.",
            main_menu(),
        )


# =========================
# VALIDATION / REJET ADMIN
# =========================
def handle_callback(callback):
    callback_id = callback["id"]
    callback_data = callback.get("data", "")
    admin_user_id = callback.get("from", {}).get("id")

    if admin_user_id != ADMIN_ID:
        answer_callback(callback_id, "⛔ Accès réservé à l'administrateur.")
        return

    if callback_data.startswith("approve_"):
        try:
            target_id = int(callback_data.split("_", 1)[1])
        except ValueError:
            answer_callback(callback_id, "Identifiant invalide.")
            return

        if target_id not in pending_users:
            answer_callback(
                callback_id,
                "Demande introuvable ou déjà traitée.",
            )
            return

        udata = get_user_data(target_id)

        # Accorder 50 signaux supplémentaires.
        udata["limit"] += 50
        udata["approved"] = True

        remaining = max(0, udata["limit"] - udata["used"])
        target_chat_id = pending_users[target_id]["chat_id"]

        result = send_message(
            target_chat_id,
            "🎉 FÉLICITATIONS !\n\n"
            "✅ Ta demande a été validée par l'administrateur.\n"
            "🎁 50 signaux supplémentaires ont été ajoutés "
            "à ton accès.\n\n"
            f"🎟️ Signaux disponibles : {remaining}\n\n"
            "Retourne au menu pour continuer.\n"
            "⚠️ Les signaux ne garantissent aucun gain. "
            "Joue de manière responsable.",
            main_menu(),
        )

        if not result.get("ok"):
            # Ne pas confirmer la validation si le client
            # ne peut pas recevoir le message.
            udata["limit"] -= 50
            udata["approved"] = False
            answer_callback(
                callback_id,
                "Échec de l'envoi au client. Validation annulée.",
            )
            return

        del pending_users[target_id]

        answer_callback(callback_id, "Client validé : 50 signaux ajoutés.")

        send_message(
            ADMIN_ID,
            "✅ VALIDATION EFFECTUÉE\n\n"
            f"ID Telegram du client : {target_id}\n"
            "🎁 50 signaux supplémentaires accordés.\n"
            f"Signaux disponibles : {remaining}",
        )
        return

    if callback_data.startswith("reject_"):
        try:
            target_id = int(callback_data.split("_", 1)[1])
        except ValueError:
            answer_callback(callback_id, "Identifiant invalide.")
            return

        if target_id not in pending_users:
            answer_callback(
                callback_id,
                "Demande introuvable ou déjà traitée.",
            )
            return

        target_chat_id = pending_users[target_id]["chat_id"]

        result = send_message(
            target_chat_id,
            "❌ Ta demande n'a pas été validée.\n\n"
            "Vérifie les informations envoyées et contacte "
            "l'administrateur si tu souhaites des précisions.",
            main_menu(),
        )

        if result.get("ok"):
            del pending_users[target_id]
            answer_callback(callback_id, "Demande rejetée.")
            send_message(
                ADMIN_ID,
                f"❌ Demande rejetée.\nID Telegram : {target_id}",
            )
        else:
            answer_callback(
                callback_id,
                "Impossible de contacter le client. Réessaie.",
            )
        return

    answer_callback(callback_id, "Action inconnue.")


# =========================
# WEBHOOK FLASK POUR RENDER
# =========================
@app.route("/", methods=["GET"])
def home():
    return "RUBBEN226 ASSISTANT est en ligne.", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    try:
        if "callback_query" in update:
            handle_callback(update["callback_query"])

        elif "message" in update:
            handle_message(update["message"])

    except Exception:
        logger.exception("Erreur pendant le traitement Telegram")

    return jsonify({"ok": True})


# =========================
# CONFIGURATION AUTOMATIQUE WEBHOOK
# =========================
def configure_webhook():
    base_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")

    if not base_url:
        logger.warning(
            "RENDER_EXTERNAL_URL non défini. "
            "Configure le webhook manuellement si nécessaire."
        )
        return

    result = telegram(
        "setWebhook",
        {"url": f"{base_url}/webhook"},
    )

    if result.get("ok"):
        logger.info("Webhook Telegram configuré.")
    else:
        logger.error("Échec de configuration du webhook.")


configure_webhook()
