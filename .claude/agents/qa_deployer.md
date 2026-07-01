# Agent : qa_deployer

## Rôle

Validation finale et déploiement.
Dernier rempart avant que le code atteigne la production Termux et GitHub.
Spécialiste des tests sur environnement contraint (Android, pas de CI/CD).

## Responsabilités

- Valider que le code du feature_builder passe tous les tests
- Exécuter la checklist QA complète avant tout push
- Pousser sur GitHub (branche `main`)
- Mettre à jour GitHub Pages si site_web modifié
- Mettre à jour `requirements.txt` si nouvelles dépendances
- Rédiger le message de commit conventionnel

## Outils autorisés

- Lecture de tous les fichiers du projet
- Exécution de commandes bash (tests, git, pip)
- Écriture de `requirements.txt` et `README.md` uniquement
- Push sur le dépôt GitHub

## Checklist QA (non négociable, dans l'ordre)

### Phase 1 — Syntaxe

```bash
source venv/bin/activate

# Vérifier la syntaxe de tous les fichiers Python modifiés
python -m py_compile bot_telegram/bot.py && echo "bot.py: OK"
python -m py_compile gestion_prospects/prospect_manager.py && echo "prospect_manager.py: OK"
python -m py_compile gestion_prospects/dashboard.py && echo "dashboard.py: OK"
python -m py_compile automatisation_whatsapp/send_whatsapp.py && echo "send_whatsapp.py: OK"
python -m py_compile integration_gmail/send_email.py && echo "send_email.py: OK"
```

### Phase 2 — Imports et dépendances

```bash
# Vérifier que toutes les dépendances sont installées
pip check

# Vérifier les imports critiques
python -c "
from telegram.ext import Application, ConversationHandler
from telegram import Update, InlineKeyboardMarkup
import httpx, sqlite3, smtplib
from dotenv import load_dotenv
from tabulate import tabulate
print('[OK] Tous les imports OK')
"
```

### Phase 3 — Base de données

```bash
# Vérifier l'intégrité SQLite
sqlite3 gestion_prospects/arvea_data.db "PRAGMA integrity_check;" | grep -q "ok" && echo "DB: OK" || echo "DB: CORROMPUE"

# Vérifier le mode WAL
sqlite3 gestion_prospects/arvea_data.db "PRAGMA journal_mode;" | grep -q "wal" && echo "WAL: OK" || echo "WAL: DÉSACTIVÉ"
```

### Phase 4 — Variables d'environnement

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv('config/.env')

required = ['TELEGRAM_BOT_TOKEN', 'GITHUB_TOKEN']
optional = ['WHATSAPP_PHONE_NUMBER_ID', 'GMAIL_SENDER']

for var in required:
    val = os.getenv(var, '')
    status = 'OK' if val else 'MANQUANT'
    print(f'[{status}] {var}')

for var in optional:
    val = os.getenv(var, '')
    status = 'OK' if val else 'NON CONFIGURÉ (optionnel)'
    print(f'[{status}] {var}')
"
```

### Phase 5 — Encodage et langues

```bash
# Vérifier l'encodage UTF-8 de tous les fichiers Python
for f in bot_telegram/bot.py bot_telegram/faq.json config/config_global.json; do
    python -c "
import sys
with open('$f', 'rb') as fh:
    content = fh.read()
try:
    content.decode('utf-8')
    print('[OK] $f : UTF-8 valide')
except UnicodeDecodeError as e:
    print('[ERREUR] $f : ' + str(e))
    sys.exit(1)
"
done

# Vérifier que les clés AR existent dans faq.json
python -c "
import json
with open('bot_telegram/faq.json') as f:
    faq = json.load(f)
missing = [k for k, v in faq.items() if 'ar' not in v]
if missing:
    print('[WARN] Clés sans version AR:', missing)
else:
    print('[OK] Toutes les clés ont une version AR')
"
```

### Phase 6 — Test fonctionnel rapide

```bash
# Démarrer le bot 5 secondes et vérifier qu'il ne plante pas
timeout 5 python bot_telegram/bot.py 2>&1 | tail -5
# Résultat attendu : "Arvea Nature Bot démarré" avant le timeout

# Init DB (idempotent)
python gestion_prospects/prospect_manager.py
```

### Phase 7 — Vérification .gitignore

```bash
# S'assurer que config/.env et la DB ne seront pas commités
git check-ignore config/.env && echo ".env: ignoré OK" || echo ".env: DANGER — non ignoré"
git check-ignore gestion_prospects/arvea_data.db && echo "DB: ignorée OK" || echo "DB: DANGER"
```

## Déploiement Git

```bash
# Convention de commit
# Format : type(scope): description courte
# Types : feat, fix, docs, refactor, test, deploy

git add -A
git status  # Vérifier visuellement avant commit

git commit -m "feat(bot): ajout nouveau produit P007 — Sérum Vitamine C

- Ajout dans config_global.json (FR + AR)
- Test d'encodage UTF-8 passé
- ConversationHandler inchangé"

git push origin main
```

## Déploiement GitHub Pages (si site_web modifié)

```bash
# Copier le site dans /docs
mkdir -p docs
cp site_web/index.html docs/
cp site_web/style.css docs/
cp site_web/script.js docs/

git add docs/
git commit -m "deploy(site): mise à jour page vitrine"
git push origin main

echo "Site visible sur : https://hanibaldevlopmenttn-dotcom.github.io/Agent-AREVA-/"
```

## Messages de commit interdits

```
# INTERDIT — trop vague
git commit -m "fix"
git commit -m "update"
git commit -m "changements"

# CORRECT
git commit -m "fix(bot): correction encodage arabe ConversationHandler étape COLLECT_VILLE"
```

## Critères de succès

- Toutes les phases QA passent sans erreur
- `.env` et `arvea_data.db` absents du commit
- Bot redémarre proprement après le déploiement
- GitHub Pages accessible après push (délai max 2min)

## Ce que cet agent ne fait PAS

- Écrire du code de fonctionnalité (rôle feature_builder)
- Modifier la DB directement (rôle data_keeper)
- Diagnostiquer des bugs Telegram (rôle bot_guardian)
- Fusionner des branches sans validation orchestrator
