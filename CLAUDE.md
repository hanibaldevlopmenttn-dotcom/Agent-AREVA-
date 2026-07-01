# CLAUDE.md — Arvea Nature Automation Project

## Contexte

**Entreprise :** Arvea Nature (Tunisie) — cosmétique & bien-être naturel
**Bot Telegram :** @orchestre_tilisi_bot
**Dépôt :** https://github.com/hanibaldevlopmenttn-dotcom/Agent-AREVA-.git
**Environnement :** Android Termux (Python 3.10+, pas de serveur payant)

## Langues

Toujours produire réponses et logs en **Français** et **Arabe tunisien (Derja)**.
Vérifier l'encodage UTF-8 sur chaque fichier modifié.

## Produits (prix fixes — ne jamais modifier sans validation)

| ID   | Nom                        | Prix TND |
|------|----------------------------|----------|
| P001 | Collagène Marin            | 85       |
| P002 | Brûle Graisse Naturel      | 65       |
| P003 | Huile d'Argan Pure         | 45       |
| P004 | Complément Multivitaminé   | 55       |
| P005 | Tisane Détox               | 35       |
| P006 | Crème Anti-Âge Naturelle   | 95       |

## Architecture fichiers critiques

```
config/.env              ← JAMAIS versionner, JAMAIS afficher
gestion_prospects/
  prospect_manager.py    ← Source de vérité SQLite (WAL mode)
  arvea_data.db          ← Base de données (JAMAIS modifier manuellement)
bot_telegram/
  bot.py                 ← ConversationHandler 8 états (modifier avec précaution)
  faq.json               ← Réponses multilingues
```

## Contraintes absolues

- Architecture **zero-cost** : GitHub Pages, Telegram API, SQLite3, Gmail SMTP
- Pas de Docker, pas de serveur payant, pas de Redis
- SQLite en mode WAL — ne jamais passer en journal_mode=DELETE
- python-telegram-bot v20+ uniquement (API async obligatoire)
- Tokens dans `config/.env` uniquement — jamais en dur dans le code

## Workflow des agents

```
orchestrator
    ├── bot_guardian    (surveillance prod Telegram)
    ├── data_keeper     (intégrité SQLite + prospects)
    ├── channel_router  (cohérence WhatsApp/Gmail/Telegram)
    ├── feature_builder (nouvelles fonctionnalités)
    └── qa_deployer     (tests + GitHub + GitHub Pages)
```

## Commandes de base (Termux)

```bash
source venv/bin/activate
python bot_telegram/bot.py          # Lancer le bot
python gestion_prospects/dashboard.py  # Dashboard
python gestion_prospects/prospect_manager.py  # Init DB
```
