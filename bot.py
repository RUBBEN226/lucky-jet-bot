import asyncio
import datetime
import json
import websockets
import requests

CONFIG = {
    "promoCode": "RUBB225",
    "registrationLink": "https://1win.ci/casino?p=4kpi",
    "apiUrl": "wss://api.example.com/luckyjet",
    "targetMultiplier": 1.50,
    "telegramToken": "8814245354:AAFh1xQaOWdnQhMM-lzq2xBaZ9etdXA5W6c",
    "telegramChatId": "8286650559"
}

class LuckyJetBot:
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] [BOT] Démarrage réussi avec le code promo : {CONFIG['promoCode']}")
        
        welcome_message = (
            f"🚀 **Bienvenue sur le Bot Lucky Jet !**\n"
            f"📅 Date de démarrage : {current_time}\n\n"
            f"⚠️ **Condition d'accès :**\n"
            f"Pour accéder au bot et recevoir les signaux, vous devez obligatoirement :\n"
            f"1. Vous inscrire via notre lien officiel : {CONFIG['registrationLink']}\n"
            f"2. Utiliser le code promo : `{CONFIG['promoCode']}`\n"
            f"3. Effectuer votre premier dépôt pour valider votre compte.\n\n"
            f"🛡️ **Jeu Responsable :**\n"
            f"Le jeu comporte des risques. Ne jouez jamais avec de l'argent dont vous avez besoin pour vos besoins essentiels, et ne jouez jamais sous le coup des émotions. Restez maître de vous !\n\n"
            f"Bonne chance à tous !"
        )
        self.send_telegram_message(welcome_message)
        await self.connect_websocket()

    def send_telegram_message(self, message):
        try:
            url = f"https://api.telegram.org/bot{CONFIG['telegramToken']}/sendMessage"
            payload = {
                "chat_id": CONFIG['telegramChatId'],
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{current_time}] [TELEGRAM] Erreur d'envoi : {e}")

    async def connect_websocket(self):
        while self.is_running:
            try:
                async with websockets.connect(CONFIG["apiUrl"]) as ws:
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{current_time}] [SOCKET] Connecté au serveur Lucky Jet.")
                    async for message in ws:
                        await self.handle_game_data(json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] [SOCKET] Connexion perdue. Reconnexion dans 5 secondes...")
                await asyncio.sleep(5)
            except Exception as e:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] [SOCKET] Erreur : {e}")
                await asyncio.sleep(5)

    async def handle_game_data(self, packet):
        if packet.get("event") == "crash":
            multiplier = packet.get('multiplier', 0)
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{current_time}] [JEU] Vol terminé à {multiplier}x")
            
            if multiplier and float(multiplier) < CONFIG["targetMultiplier"]:
                msg = (
                    f"⚠️ Crash bas ({multiplier}x) à {current_time}.\n"
                    f"Rappel : Jouez avec modération et gardez le contrôle de vos émotions.\n"
                    f"Inscrivez-vous sur {CONFIG['registrationLink']} avec le code `{CONFIG['promoCode']}` "
                    f"et faites un dépôt pour continuer à profiter du bot en toute sécurité !"
                )
                print(f"[ASTUCE] {msg}")
                self.send_telegram_message(msg)

async def main():
    bot = LuckyJetBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
