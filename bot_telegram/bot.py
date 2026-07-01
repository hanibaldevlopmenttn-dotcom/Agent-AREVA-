import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / "config" / ".env")

sys.path.insert(0, str(BASE_DIR))

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

from gestion_prospects.prospect_manager import (
    init_db, upsert_prospect, get_prospect_by_telegram_id,
    create_commande, get_commandes_by_prospect, log_interaction, get_stats
)

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(BASE_DIR / "bot_telegram" / "bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

FAQ_PATH = Path(__file__).resolve().parent / "faq.json"
with open(FAQ_PATH, "r", encoding="utf-8") as f:
    FAQ = json.load(f)

CONFIG_PATH = BASE_DIR / "config" / "config_global.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

PRODUITS = {p["id"]: p for p in CONFIG["produits"]}

# ConversationHandler states
(
    COLLECT_PRENOM,
    COLLECT_NOM,
    COLLECT_TELEPHONE,
    COLLECT_VILLE,
    SELECT_PRODUIT,
    CONFIRM_QUANTITE,
    COLLECT_ADRESSE,
    CONFIRM_COMMANDE,
) = range(8)


def get_user_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("langue", "fr")


def faq_msg(key: str, lang: str) -> str:
    entry = FAQ.get(key, {})
    return entry.get(lang, entry.get("fr", "Information non disponible."))


def produits_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for pid, p in PRODUITS.items():
        label = f"{p['emoji']} {p['nom_fr']} — {p['prix_tnd']} TND"
        buttons.append([InlineKeyboardButton(label, callback_data=f"produit_{pid}")])
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="annuler")])
    return InlineKeyboardMarkup(buttons)


def langue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
            InlineKeyboardButton("🇹🇳 عربي", callback_data="lang_ar"),
        ]
    ])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = str(update.effective_user.id)
    prenom = update.effective_user.first_name or "Ami(e)"
    upsert_prospect(telegram_id=telegram_id, prenom=prenom, source="telegram")
    log_interaction(
        prospect_id=get_prospect_by_telegram_id(telegram_id)["id"],
        type_interaction="start",
        contenu="/start"
    )
    lang = get_user_lang(context)
    text = faq_msg("bonjour", lang).replace("{prenom}", prenom)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=langue_keyboard()
    )


async def cmd_aide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("aide", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_produits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    if lang == "ar":
        header = "🛍️ **منتجاتنا الطبيعية**\n\nاختر منتجاً لمعرفة المزيد أو اطلبه مباشرة:"
    else:
        header = "🛍️ **Nos produits naturels**\n\nChoisissez un produit pour en savoir plus ou commander :"
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=produits_keyboard())


async def cmd_livraison(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("livraison", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_paiement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("paiement", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_retour(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("retour", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("contact", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_collagene(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("collagene", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_argan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("argan", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_brulegraisse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("brule_graisse", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_multivitamine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("multivitamine", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_tisane(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("tisane", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_creme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(context)
    await update.message.reply_text(faq_msg("creme", lang), parse_mode=ParseMode.MARKDOWN)


async def cmd_fr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["langue"] = "fr"
    telegram_id = str(update.effective_user.id)
    upsert_prospect(telegram_id=telegram_id, langue="fr")
    await update.message.reply_text("✅ Langue changée en **Français** 🇫🇷", parse_mode=ParseMode.MARKDOWN)


async def cmd_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["langue"] = "ar"
    telegram_id = str(update.effective_user.id)
    upsert_prospect(telegram_id=telegram_id, langue="ar")
    await update.message.reply_text("✅ تم تغيير اللغة إلى **العربية** 🇹🇳", parse_mode=ParseMode.MARKDOWN)


# ─── CONVERSATION COMMANDE ───────────────────────────────────────────────────

async def conv_commande_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = str(update.effective_user.id)
    prospect = get_prospect_by_telegram_id(telegram_id)
    lang = get_user_lang(context)

    if not prospect:
        upsert_prospect(telegram_id=telegram_id, prenom=update.effective_user.first_name)
        prospect = get_prospect_by_telegram_id(telegram_id)

    context.user_data["commande"] = {}

    if prospect.get("nom") and prospect.get("telephone"):
        context.user_data["commande"]["prospect_id"] = prospect["id"]
        context.user_data["commande"]["nom"] = prospect["nom"]
        context.user_data["commande"]["prenom"] = prospect.get("prenom", "")
        context.user_data["commande"]["telephone"] = prospect["telephone"]
        context.user_data["commande"]["ville"] = prospect.get("ville", "")

        if lang == "ar":
            msg = f"👋 مرحباً {prospect.get('prenom', '')} !\n\nاختر المنتج الذي تريد طلبه:"
        else:
            msg = f"👋 Bonjour {prospect.get('prenom', '')} !\n\nChoisissez le produit que vous souhaitez commander :"
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=produits_keyboard())
        return SELECT_PRODUIT
    else:
        if lang == "ar":
            msg = "🛒 **طلب جديد**\n\nما هو اسمك الأول؟"
        else:
            msg = "🛒 **Nouvelle commande**\n\nQuel est votre prénom ?"
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return COLLECT_PRENOM


async def conv_collect_prenom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prenom = update.message.text.strip()
    context.user_data["commande"]["prenom"] = prenom
    lang = get_user_lang(context)
    if lang == "ar":
        await update.message.reply_text(f"شكراً {prenom}! ما هو لقبك؟")
    else:
        await update.message.reply_text(f"Merci {prenom} ! Quel est votre nom de famille ?")
    return COLLECT_NOM


async def conv_collect_nom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nom = update.message.text.strip()
    context.user_data["commande"]["nom"] = nom
    lang = get_user_lang(context)
    if lang == "ar":
        await update.message.reply_text("ما هو رقم هاتفك؟ (مثال: +21699000000)")
    else:
        await update.message.reply_text("Quel est votre numéro de téléphone ? (ex: +21699000000)")
    return COLLECT_TELEPHONE


async def conv_collect_telephone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telephone = update.message.text.strip()
    if len(telephone) < 8:
        lang = get_user_lang(context)
        if lang == "ar":
            await update.message.reply_text("⚠️ رقم الهاتف غير صحيح. أعد المحاولة:")
        else:
            await update.message.reply_text("⚠️ Numéro invalide. Veuillez réessayer :")
        return COLLECT_TELEPHONE

    context.user_data["commande"]["telephone"] = telephone
    lang = get_user_lang(context)

    keyboard = ReplyKeyboardMarkup(
        [["Tunis", "Sfax"], ["Sousse", "Bizerte"], ["Autre / أخرى"]],
        resize_keyboard=True, one_time_keyboard=True
    )
    if lang == "ar":
        await update.message.reply_text("ما هي مدينتك؟", reply_markup=keyboard)
    else:
        await update.message.reply_text("Quelle est votre ville ?", reply_markup=keyboard)
    return COLLECT_VILLE


async def conv_collect_ville(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ville = update.message.text.strip()
    context.user_data["commande"]["ville"] = ville
    telegram_id = str(update.effective_user.id)

    prospect_id = upsert_prospect(
        telegram_id=telegram_id,
        prenom=context.user_data["commande"].get("prenom"),
        nom=context.user_data["commande"].get("nom"),
        telephone=context.user_data["commande"].get("telephone"),
        ville=ville,
        statut="prospect_qualifie"
    )
    context.user_data["commande"]["prospect_id"] = prospect_id

    lang = get_user_lang(context)
    if lang == "ar":
        msg = "اختر المنتج الذي تريد طلبه:"
    else:
        msg = "Choisissez le produit que vous souhaitez commander :"
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text("⬇️", reply_markup=produits_keyboard())
    return SELECT_PRODUIT


async def conv_select_produit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "annuler":
        lang = context.user_data.get("langue", "fr")
        msg = "تم إلغاء الطلب." if lang == "ar" else "Commande annulée."
        await query.edit_message_text(msg)
        context.user_data.pop("commande", None)
        return ConversationHandler.END

    if data.startswith("produit_"):
        produit_id = data.replace("produit_", "")
        produit = PRODUITS.get(produit_id)
        if not produit:
            await query.edit_message_text("❌ Produit introuvable.")
            return ConversationHandler.END

        context.user_data["commande"]["produit_id"] = produit_id
        context.user_data["commande"]["produit"] = produit
        lang = context.user_data.get("langue", "fr")

        if lang == "ar":
            msg = (
                f"{produit['emoji']} **{produit['nom_ar']}**\n"
                f"💰 السعر: {produit['prix_tnd']} دينار\n\n"
                f"{produit['description_ar']}\n\n"
                f"كم وحدة تريد؟ (اكتب رقماً من 1 إلى 10)"
            )
        else:
            msg = (
                f"{produit['emoji']} **{produit['nom_fr']}**\n"
                f"💰 Prix : {produit['prix_tnd']} TND\n\n"
                f"{produit['description_fr']}\n\n"
                f"Quelle quantité souhaitez-vous ? (Tapez un chiffre de 1 à 10)"
            )
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
        return CONFIRM_QUANTITE

    return SELECT_PRODUIT


async def conv_confirm_quantite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        quantite = int(update.message.text.strip())
        if quantite < 1 or quantite > 10:
            raise ValueError
    except ValueError:
        lang = get_user_lang(context)
        msg = "⚠️ عدد غير صالح. أدخل رقماً من 1 إلى 10." if lang == "ar" else "⚠️ Quantité invalide. Entrez un chiffre de 1 à 10."
        await update.message.reply_text(msg)
        return CONFIRM_QUANTITE

    context.user_data["commande"]["quantite"] = quantite
    lang = get_user_lang(context)
    if lang == "ar":
        await update.message.reply_text("ما هو عنوان التسليم؟ (المدينة، الشارع، المنزل)")
    else:
        await update.message.reply_text("Quelle est votre adresse de livraison complète ? (Ville, Rue, N° Appart)")
    return COLLECT_ADRESSE


async def conv_collect_adresse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    adresse = update.message.text.strip()
    context.user_data["commande"]["adresse"] = adresse
    lang = get_user_lang(context)

    cmd = context.user_data["commande"]
    produit = cmd["produit"]
    quantite = cmd["quantite"]
    total = produit["prix_tnd"] * quantite

    if lang == "ar":
        summary = (
            f"📋 **ملخص الطلب**\n\n"
            f"👤 الاسم: {cmd.get('prenom', '')} {cmd.get('nom', '')}\n"
            f"📱 الهاتف: {cmd.get('telephone', '')}\n"
            f"📍 العنوان: {adresse}\n"
            f"{'─'*30}\n"
            f"{produit['emoji']} {produit['nom_ar']}\n"
            f"🔢 الكمية: {quantite}\n"
            f"💰 المجموع: **{total:.2f} دينار**\n\n"
            f"هل تأكد الطلب؟"
        )
        buttons = [
            [InlineKeyboardButton("✅ تأكيد", callback_data="confirm_oui")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="confirm_non")],
        ]
    else:
        summary = (
            f"📋 **Récapitulatif de commande**\n\n"
            f"👤 Nom : {cmd.get('prenom', '')} {cmd.get('nom', '')}\n"
            f"📱 Téléphone : {cmd.get('telephone', '')}\n"
            f"📍 Adresse : {adresse}\n"
            f"{'─'*30}\n"
            f"{produit['emoji']} {produit['nom_fr']}\n"
            f"🔢 Quantité : {quantite}\n"
            f"💰 Total : **{total:.2f} TND**\n\n"
            f"Confirmez-vous votre commande ?"
        )
        buttons = [
            [InlineKeyboardButton("✅ Confirmer", callback_data="confirm_oui")],
            [InlineKeyboardButton("❌ Annuler", callback_data="confirm_non")],
        ]

    await update.message.reply_text(
        summary,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CONFIRM_COMMANDE


async def conv_confirm_commande(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("langue", "fr")

    if query.data == "confirm_non":
        msg = "تم إلغاء طلبك." if lang == "ar" else "Votre commande a été annulée."
        await query.edit_message_text(msg)
        context.user_data.pop("commande", None)
        return ConversationHandler.END

    cmd = context.user_data["commande"]
    produit = cmd["produit"]
    quantite = cmd["quantite"]
    total = produit["prix_tnd"] * quantite

    commande_id = create_commande(
        prospect_id=cmd["prospect_id"],
        produit_id=cmd["produit_id"],
        produit_nom=produit["nom_fr"],
        prix_unitaire=produit["prix_tnd"],
        quantite=quantite,
        adresse_livraison=cmd.get("adresse"),
    )

    upsert_prospect(
        telegram_id=str(update.effective_user.id),
        statut="client"
    )

    log_interaction(
        prospect_id=cmd["prospect_id"],
        type_interaction="commande",
        contenu=f"CMD-{commande_id:05d} | {produit['nom_fr']} x{quantite} | {total:.2f} TND"
    )

    if lang == "ar":
        msg = (
            f"✅ **تم تسجيل طلبك بنجاح!**\n\n"
            f"🔖 المرجع: CMD-{commande_id:05d}\n"
            f"📦 {produit['nom_ar']} × {quantite}\n"
            f"💰 الإجمالي: {total:.2f} دينار\n\n"
            f"سيتصل بك فريقنا خلال 24 ساعة لتأكيد التوصيل.\n"
            f"شكراً لثقتك! 🌿"
        )
    else:
        msg = (
            f"✅ **Commande enregistrée avec succès !**\n\n"
            f"🔖 Référence : CMD-{commande_id:05d}\n"
            f"📦 {produit['nom_fr']} × {quantite}\n"
            f"💰 Total : {total:.2f} TND\n\n"
            f"Notre équipe vous contactera sous 24h pour organiser la livraison.\n"
            f"Merci de votre confiance ! 🌿"
        )

    await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
    context.user_data.pop("commande", None)
    return ConversationHandler.END


async def conv_annuler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_user_lang(context)
    msg = "تم إلغاء العملية." if lang == "ar" else "Opération annulée."
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    context.user_data.pop("commande", None)
    return ConversationHandler.END


async def callback_langue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "lang_fr":
        context.user_data["langue"] = "fr"
        telegram_id = str(update.effective_user.id)
        upsert_prospect(telegram_id=telegram_id, langue="fr")
        await query.edit_message_text(
            faq_msg("bonjour", "fr"),
            parse_mode=ParseMode.MARKDOWN
        )
    elif query.data == "lang_ar":
        context.user_data["langue"] = "ar"
        telegram_id = str(update.effective_user.id)
        upsert_prospect(telegram_id=telegram_id, langue="ar")
        await query.edit_message_text(
            faq_msg("bonjour", "ar"),
            parse_mode=ParseMode.MARKDOWN
        )


async def callback_produit_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = context.user_data.get("langue", "fr")

    produit_faq_map = {
        "P001": "collagene",
        "P002": "brule_graisse",
        "P003": "argan",
        "P004": "multivitamine",
        "P005": "tisane",
        "P006": "creme",
    }

    if data.startswith("produit_"):
        pid = data.replace("produit_", "")
        faq_key = produit_faq_map.get(pid)
        if faq_key:
            await query.edit_message_text(faq_msg(faq_key, lang), parse_mode=ParseMode.MARKDOWN)
    elif data == "annuler":
        msg = "تم الإلغاء." if lang == "ar" else "Opération annulée."
        await query.edit_message_text(msg)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower().strip()
    lang = get_user_lang(context)

    keywords_fr = {
        "livraison": "livraison", "paiement": "paiement", "retour": "retour",
        "contact": "contact", "aide": "aide", "bonjour": "bonjour",
        "salut": "bonjour", "hello": "bonjour", "prix": "produits",
        "produit": "produits", "commander": "commande",
    }
    keywords_ar = {
        "توصيل": "livraison", "دفع": "paiement", "إرجاع": "retour",
        "تواصل": "contact", "مساعدة": "aide", "أهلا": "bonjour",
        "مرحبا": "bonjour", "سلام": "bonjour", "سعر": "produits",
        "منتج": "produits", "اطلب": "commande",
    }

    keywords = keywords_ar if lang == "ar" else keywords_fr
    matched_key = None
    for kw, faq_key in keywords.items():
        if kw in text:
            matched_key = faq_key
            break

    if matched_key == "commande":
        pass
    elif matched_key:
        await update.message.reply_text(faq_msg(matched_key, lang), parse_mode=ParseMode.MARKDOWN)
    else:
        if lang == "ar":
            await update.message.reply_text(
                "لم أفهم. استخدم /aide لرؤية الأوامر المتاحة، أو /commande لطلب منتج.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "Je n'ai pas compris. Utilisez /aide pour voir les commandes disponibles, ou /commande pour passer une commande.",
                parse_mode=ParseMode.MARKDOWN
            )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception lors du traitement d'une mise à jour:", exc_info=context.error)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN non défini dans config/.env")
        sys.exit(1)

    init_db()
    logger.info("Base de données initialisée.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    commande_conv = ConversationHandler(
        entry_points=[CommandHandler("commande", conv_commande_start)],
        states={
            COLLECT_PRENOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_collect_prenom)],
            COLLECT_NOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_collect_nom)],
            COLLECT_TELEPHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_collect_telephone)],
            COLLECT_VILLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_collect_ville)],
            SELECT_PRODUIT: [CallbackQueryHandler(conv_select_produit)],
            CONFIRM_QUANTITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_confirm_quantite)],
            COLLECT_ADRESSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_collect_adresse)],
            CONFIRM_COMMANDE: [CallbackQueryHandler(conv_confirm_commande)],
        },
        fallbacks=[CommandHandler("annuler", conv_annuler)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("aide", cmd_aide))
    app.add_handler(CommandHandler("help", cmd_aide))
    app.add_handler(CommandHandler("produits", cmd_produits))
    app.add_handler(CommandHandler("livraison", cmd_livraison))
    app.add_handler(CommandHandler("paiement", cmd_paiement))
    app.add_handler(CommandHandler("retour", cmd_retour))
    app.add_handler(CommandHandler("contact", cmd_contact))
    app.add_handler(CommandHandler("collagene", cmd_collagene))
    app.add_handler(CommandHandler("argan", cmd_argan))
    app.add_handler(CommandHandler("brulegraisse", cmd_brulegraisse))
    app.add_handler(CommandHandler("multivitamine", cmd_multivitamine))
    app.add_handler(CommandHandler("tisane", cmd_tisane))
    app.add_handler(CommandHandler("creme", cmd_creme))
    app.add_handler(CommandHandler("fr", cmd_fr))
    app.add_handler(CommandHandler("ar", cmd_ar))
    app.add_handler(commande_conv)
    app.add_handler(CallbackQueryHandler(callback_langue, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(callback_produit_info, pattern="^(produit_|annuler)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error_handler)

    logger.info("🌿 Arvea Nature Bot démarré — @orchestre_tilisi_bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
