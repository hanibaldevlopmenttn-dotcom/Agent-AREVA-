# 🌿 Arvea Nature — Agent Commercial Automatisé

Bot Telegram + Site Web statique + Dashboard terminal pour Arvea Nature (Tunisie).  
Architecture **100% gratuite**, exécution sur **smartphone Android via Termux**.

---

## 📁 Structure du projet

```
Agent-AREVA-/
├── config/
│   ├── .env                    # Tokens & secrets (non versionné)
│   └── config_global.json      # Produits, config entreprise
├── gestion_prospects/
│   ├── prospect_manager.py     # Moteur SQLite3
│   └── dashboard.py            # Dashboard terminal
├── automatisation_whatsapp/
│   └── send_whatsapp.py        # Client WhatsApp Cloud API
├── integration_gmail/
│   └── send_email.py           # Rapports email via SMTP
├── bot_telegram/
│   ├── faq.json                # Réponses FAQ (FR/AR)
│   └── bot.py                  # Bot Telegram complet
├── site_web/
│   ├── index.html              # Page vitrine responsive
│   ├── style.css               # Design mobile-first
│   ├── script.js               # Logique JS asynchrone
│   └── google_apps_script.txt  # Code Google Apps Script
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Installation complète sous Termux (Android)

### Étape 1 — Préparer Termux

```bash
# Mettre à jour les paquets
pkg update && pkg upgrade -y

# Installer les dépendances système
pkg install python git openssl-dev libffi-dev -y

# Vérifier la version Python (doit être ≥ 3.10)
python --version
```

### Étape 2 — Cloner le dépôt

```bash
# Configurer Git
git config --global user.name "VotreNom"
git config --global user.email "votre@email.com"

# Cloner via HTTPS (recommandé sur Termux)
git clone https://github.com/hanibaldevlopmenttn-dotcom/Agent-AREVA-.git

# Ou via SSH (si clé SSH configurée)
# git clone git@github.com:hanibaldevlopmenttn-dotcom/Agent-AREVA-.git

cd Agent-AREVA-
```

### Étape 3 — Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate
```

### Étape 4 — Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 5 — Configurer les variables d'environnement

Le fichier `config/.env` est déjà pré-configuré avec les tokens Telegram et GitHub.  
Complétez les champs optionnels si nécessaire :

```bash
nano config/.env
```

Variables à renseigner selon vos besoins :

| Variable | Description | Requis |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ Déjà configuré | Oui |
| `GITHUB_TOKEN` | ✅ Déjà configuré | Oui |
| `WHATSAPP_PHONE_NUMBER_ID` | ID du numéro WhatsApp Business | Optionnel |
| `WHATSAPP_ACCESS_TOKEN` | Token API Meta Cloud | Optionnel |
| `GMAIL_SENDER` | Adresse Gmail expéditeur | Optionnel |
| `GMAIL_APP_PASSWORD` | Mot de passe d'application Gmail | Optionnel |
| `GMAIL_RECIPIENT` | Adresse de réception des rapports | Optionnel |
| `GOOGLE_SHEETS_WEBAPP_URL` | URL de déploiement Google Apps Script | Optionnel |

### Étape 6 — Initialiser la base de données

```bash
python gestion_prospects/prospect_manager.py
# → [OK] Base de données initialisée : .../arvea_data.db
```

### Étape 7 — Lancer le bot Telegram

```bash
python bot_telegram/bot.py
# → 🌿 Arvea Nature Bot démarré — @orchestre_tilisi_bot
```

**Pour maintenir le bot actif en arrière-plan :**

```bash
# Option 1 : nohup
nohup python bot_telegram/bot.py > bot_telegram/bot.log 2>&1 &
echo "PID: $!"

# Option 2 : tmux (installer d'abord : pkg install tmux)
tmux new -s arvea_bot
python bot_telegram/bot.py
# Ctrl+B puis D pour détacher
```

### Étape 8 — Lancer le dashboard

```bash
python gestion_prospects/dashboard.py
```

---

## 🌐 Déploiement du site web (GitHub Pages)

### Option A — Via ligne de commande

```bash
cd site_web

# Copier les fichiers à la racine ou dans un dossier docs/
cp -r . ../docs/

cd ..
git add docs/
git commit -m "deploy: site web Arvea Nature"
git push origin main
```

### Option B — Configuration GitHub Pages

1. Aller sur : `https://github.com/hanibaldevlopmenttn-dotcom/Agent-AREVA-/settings/pages`
2. Source : **Deploy from a branch**
3. Branch : `main` / dossier : `/docs`
4. Cliquer **Save**

Site accessible sur : `https://hanibaldevlopmenttn-dotcom.github.io/Agent-AREVA-/`

---

## 📊 Google Apps Script (Google Sheets)

1. Ouvrir `site_web/google_apps_script.txt`
2. Aller sur : https://script.google.com → Nouveau projet
3. Coller le code, remplacer `VOTRE_GOOGLE_SHEET_ID_ICI`
4. Déployer → Application Web → Accès : Tout le monde
5. Copier l'URL dans `site_web/script.js` → variable `GOOGLE_SHEETS_URL`

---

## 💬 Commandes du Bot Telegram

| Commande | Description |
|---|---|
| `/start` | Message de bienvenue + choix de langue |
| `/produits` | Catalogue des 6 produits |
| `/commande` | Démarrer une commande (ConversationHandler) |
| `/livraison` | Infos livraison |
| `/paiement` | Modes de paiement |
| `/retour` | Politique de retour |
| `/contact` | Coordonnées |
| `/collagene` | Fiche Collagène Marin |
| `/argan` | Fiche Huile d'Argan |
| `/brulegraisse` | Fiche Brûle Graisse |
| `/multivitamine` | Fiche Multivitamines |
| `/tisane` | Fiche Tisane Détox |
| `/creme` | Fiche Crème Anti-Âge |
| `/fr` | Passer en français |
| `/ar` | Passer en arabe (Derja) |
| `/annuler` | Annuler la commande en cours |

---

## 🛒 Catalogue produits

| # | Produit | Prix |
|---|---|---|
| P001 | 🐟 Collagène Marin | **85 TND** |
| P002 | 🔥 Brûle Graisse Naturel | **65 TND** |
| P003 | ✨ Huile d'Argan Pure | **45 TND** |
| P004 | 💊 Complément Multivitaminé | **55 TND** |
| P005 | 🌿 Tisane Détox | **35 TND** |
| P006 | 🌸 Crème Anti-Âge Naturelle | **95 TND** |

---

## 🔧 Commandes utiles

```bash
# Voir les logs du bot
tail -f bot_telegram/bot.log

# Arrêter le bot (si nohup)
kill $(pgrep -f "bot.py")

# Mettre à jour le dépôt
git pull origin main

# Synchroniser vers GitHub
git add .
git commit -m "update: $(date '+%d/%m/%Y %H:%M')"
git push origin main

# Relancer après crash
source venv/bin/activate && python bot_telegram/bot.py
```

---

## 🔒 Sécurité

- Le fichier `config/.env` est dans `.gitignore` — il ne sera **jamais** poussé sur GitHub.
- Pour générer un App Password Gmail : [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- La base SQLite3 (`arvea_data.db`) utilise le mode WAL pour éviter les conflits en lecture/écriture concurrent.

---

## 📞 Support

- 🤖 Bot : [@orchestre_tilisi_bot](https://t.me/orchestre_tilisi_bot)
- 🐙 GitHub : [hanibaldevlopmenttn-dotcom/Agent-AREVA-](https://github.com/hanibaldevlopmenttn-dotcom/Agent-AREVA-)

---

*Fait avec 💚 pour Arvea Nature — Tunisie 🇹🇳*
