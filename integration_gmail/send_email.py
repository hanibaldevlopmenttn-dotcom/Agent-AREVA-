import smtplib
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / "config" / ".env")

GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT", "")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _create_smtp_connection():
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        raise ValueError("GMAIL_SENDER et GMAIL_APP_PASSWORD doivent être configurés dans config/.env")
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
    return server


def send_email(to: str, subject: str, body_html: str, body_text: str = None,
               attachment_path: Path = None) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Arvea Nature Bot <{GMAIL_SENDER}>"
        msg["To"] = to
        msg["Subject"] = subject

        if body_text:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={Path(attachment_path).name}")
            msg.attach(part)

        with _create_smtp_connection() as server:
            server.sendmail(GMAIL_SENDER, to, msg.as_string())

        print(f"[OK] Email envoyé à {to} | Sujet : {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[ERREUR] Authentification Gmail échouée. Vérifiez GMAIL_SENDER et GMAIL_APP_PASSWORD.")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERREUR] SMTP : {e}")
        return False
    except ValueError as e:
        print(f"[ERREUR] Configuration : {e}")
        return False


def send_rapport_journalier(stats: dict, recipient: str = None) -> bool:
    to = recipient or GMAIL_RECIPIENT
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    date_label = datetime.now().strftime("%d/%m/%Y")

    commandes_html = ""
    for statut, nb in stats.get("commandes_par_statut", {}).items():
        commandes_html += f"<tr><td style='padding:6px 12px;'>{statut.replace('_', ' ').title()}</td><td style='padding:6px 12px; text-align:center;'><strong>{nb}</strong></td></tr>"

    top_produits_html = ""
    for i, p in enumerate(stats.get("top_produits", []), 1):
        top_produits_html += f"<tr><td style='padding:6px 12px;'>{i}. {p['produit_nom']}</td><td style='padding:6px 12px; text-align:center;'>{p['nb']} ventes</td><td style='padding:6px 12px; text-align:right;'>{p['total']:.2f} TND</td></tr>"

    body_html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="UTF-8"><title>Rapport Arvea Nature</title></head>
    <body style="font-family: Arial, sans-serif; background:#f4f4f4; margin:0; padding:20px;">
      <div style="max-width:600px; margin:auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #2d6a4f, #52b788); padding:24px; text-align:center;">
          <h1 style="color:#fff; margin:0; font-size:22px;">🌿 Arvea Nature</h1>
          <p style="color:#d8f3dc; margin:6px 0 0;">Rapport journalier — {date_label}</p>
        </div>
        <div style="padding:24px;">
          <h2 style="color:#2d6a4f; border-bottom:2px solid #d8f3dc; padding-bottom:8px;">📊 Indicateurs clés</h2>
          <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
            <tr style="background:#f0faf0;">
              <td style="padding:12px; font-weight:bold; color:#555;">👥 Total Prospects</td>
              <td style="padding:12px; font-size:20px; font-weight:bold; color:#2d6a4f; text-align:right;">{stats['total_prospects']}</td>
            </tr>
            <tr>
              <td style="padding:12px; font-weight:bold; color:#555;">🛒 Total Commandes</td>
              <td style="padding:12px; font-size:20px; font-weight:bold; color:#2d6a4f; text-align:right;">{stats['total_commandes']}</td>
            </tr>
            <tr style="background:#f0faf0;">
              <td style="padding:12px; font-weight:bold; color:#555;">💰 Chiffre d'Affaires</td>
              <td style="padding:12px; font-size:20px; font-weight:bold; color:#52b788; text-align:right;">{stats['chiffre_affaires_tnd']:.2f} TND</td>
            </tr>
          </table>

          <h2 style="color:#2d6a4f; border-bottom:2px solid #d8f3dc; padding-bottom:8px;">📦 Commandes par statut</h2>
          <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
            <thead><tr style="background:#2d6a4f; color:#fff;">
              <th style="padding:8px 12px; text-align:left;">Statut</th>
              <th style="padding:8px 12px; text-align:center;">Nombre</th>
            </tr></thead>
            <tbody>{commandes_html}</tbody>
          </table>

          <h2 style="color:#2d6a4f; border-bottom:2px solid #d8f3dc; padding-bottom:8px;">🏆 Top Produits</h2>
          <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
            <thead><tr style="background:#2d6a4f; color:#fff;">
              <th style="padding:8px 12px; text-align:left;">Produit</th>
              <th style="padding:8px 12px; text-align:center;">Ventes</th>
              <th style="padding:8px 12px; text-align:right;">CA (TND)</th>
            </tr></thead>
            <tbody>{top_produits_html}</tbody>
          </table>

          <p style="color:#888; font-size:12px; text-align:center; margin-top:20px;">
            Rapport généré automatiquement le {now} par Arvea Nature Bot 🤖
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    body_text = (
        f"Rapport Arvea Nature — {date_label}\n"
        f"{'='*40}\n"
        f"Prospects : {stats['total_prospects']}\n"
        f"Commandes : {stats['total_commandes']}\n"
        f"CA Total  : {stats['chiffre_affaires_tnd']:.2f} TND\n"
        f"{'='*40}\n"
        f"Généré le {now}"
    )

    return send_email(
        to=to,
        subject=f"📊 Rapport Arvea Nature — {date_label}",
        body_html=body_html,
        body_text=body_text
    )


def send_confirmation_commande_email(to: str, client_nom: str, produit_nom: str,
                                      prix_total: float, commande_id: int,
                                      adresse: str = "Non renseignée") -> bool:
    body_html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:20px;">
      <div style="max-width:520px; margin:auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#2d6a4f,#52b788); padding:20px; text-align:center;">
          <h1 style="color:#fff; margin:0;">✅ Commande Confirmée</h1>
          <p style="color:#d8f3dc; margin:4px 0 0;">Arvea Nature</p>
        </div>
        <div style="padding:24px;">
          <p>Bonjour <strong>{client_nom}</strong>,</p>
          <p>Votre commande a bien été enregistrée. Voici le récapitulatif :</p>
          <table style="width:100%; border-collapse:collapse; margin:16px 0;">
            <tr style="background:#f0faf0;"><td style="padding:10px;"><strong>Référence</strong></td><td style="padding:10px;">CMD-{commande_id:05d}</td></tr>
            <tr><td style="padding:10px;"><strong>Produit</strong></td><td style="padding:10px;">{produit_nom}</td></tr>
            <tr style="background:#f0faf0;"><td style="padding:10px;"><strong>Montant</strong></td><td style="padding:10px; color:#2d6a4f; font-weight:bold;">{prix_total:.2f} TND</td></tr>
            <tr><td style="padding:10px;"><strong>Livraison</strong></td><td style="padding:10px;">{adresse}</td></tr>
          </table>
          <p>Notre équipe vous contactera sous <strong>24h</strong> pour organiser la livraison.</p>
          <p style="color:#888; font-size:12px; margin-top:20px;">Merci de votre confiance 🌿<br><strong>L'équipe Arvea Nature</strong></p>
        </div>
      </div>
    </body>
    </html>
    """
    return send_email(
        to=to,
        subject=f"✅ Confirmation commande CMD-{commande_id:05d} — Arvea Nature",
        body_html=body_html
    )


if __name__ == "__main__":
    test_stats = {
        "total_prospects": 42,
        "total_commandes": 17,
        "chiffre_affaires_tnd": 1245.50,
        "commandes_par_statut": {"en_attente": 5, "confirmee": 8, "livree": 4},
        "top_produits": [
            {"produit_nom": "Collagène Marin", "nb": 7, "total": 595.0},
            {"produit_nom": "Crème Anti-Âge", "nb": 5, "total": 475.0},
        ]
    }
    send_rapport_journalier(test_stats)
