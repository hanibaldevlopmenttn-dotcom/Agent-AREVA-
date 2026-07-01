import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / "config" / ".env")

WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")

BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def send_text_message(to: str, message: str) -> dict:
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        return {"error": "WhatsApp API non configurée. Veuillez renseigner WHATSAPP_PHONE_NUMBER_ID et WHATSAPP_ACCESS_TOKEN dans config/.env"}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(BASE_URL, headers=_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Erreur réseau: {str(e)}"}


async def send_template_message(to: str, template_name: str, language_code: str = "fr",
                                 components: list = None) -> dict:
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        return {"error": "WhatsApp API non configurée."}

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(BASE_URL, headers=_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Erreur réseau: {str(e)}"}


async def send_commande_confirmation(to: str, client_nom: str, produit_nom: str,
                                      prix_total: float, commande_id: int) -> dict:
    message = (
        f"✅ *Confirmation de commande - Arvea Nature*\n\n"
        f"Bonjour {client_nom},\n"
        f"Votre commande a bien été enregistrée !\n\n"
        f"📦 Produit : {produit_nom}\n"
        f"💰 Total : {prix_total:.2f} TND\n"
        f"🔖 Référence : CMD-{commande_id:05d}\n\n"
        f"Notre équipe vous contactera sous 24h pour confirmer la livraison.\n"
        f"Merci de votre confiance ! 🌿"
    )
    return await send_text_message(to, message)


async def send_relance_prospect(to: str, prenom: str, produit_nom: str) -> dict:
    message = (
        f"Bonjour {prenom} 👋\n\n"
        f"Nous avons remarqué votre intérêt pour *{produit_nom}*.\n"
        f"Avez-vous des questions ? Notre équipe est disponible pour vous aider ! 😊\n\n"
        f"🌿 *Arvea Nature* - Votre bien-être naturel"
    )
    return await send_text_message(to, message)


async def notify_admin_new_commande(admin_phone: str, client_nom: str,
                                     produit_nom: str, prix_total: float,
                                     ville: str = "Non renseignée") -> dict:
    message = (
        f"🔔 *Nouvelle commande reçue !*\n\n"
        f"👤 Client : {client_nom}\n"
        f"📦 Produit : {produit_nom}\n"
        f"💰 Montant : {prix_total:.2f} TND\n"
        f"📍 Ville : {ville}\n"
        f"🕐 Date : {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"👉 Vérifiez le dashboard pour traiter la commande."
    )
    return await send_text_message(admin_phone, message)


if __name__ == "__main__":
    async def test():
        result = await send_text_message("+21600000000", "Test Arvea Nature Bot")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test())
