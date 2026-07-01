import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "gestion_prospects" / "arvea_data.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            nom TEXT,
            prenom TEXT,
            telephone TEXT,
            email TEXT,
            ville TEXT,
            langue TEXT DEFAULT 'fr',
            source TEXT DEFAULT 'telegram',
            date_inscription TEXT DEFAULT (datetime('now','localtime')),
            statut TEXT DEFAULT 'nouveau',
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            produit_id TEXT NOT NULL,
            produit_nom TEXT NOT NULL,
            quantite INTEGER DEFAULT 1,
            prix_unitaire REAL NOT NULL,
            prix_total REAL NOT NULL,
            statut TEXT DEFAULT 'en_attente',
            adresse_livraison TEXT,
            date_commande TEXT DEFAULT (datetime('now','localtime')),
            date_modification TEXT DEFAULT (datetime('now','localtime')),
            notes TEXT,
            FOREIGN KEY (prospect_id) REFERENCES prospects(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            type_interaction TEXT NOT NULL,
            contenu TEXT,
            date_interaction TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (prospect_id) REFERENCES prospects(id) ON DELETE CASCADE
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_prospects_telegram_id ON prospects(telegram_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_commandes_prospect_id ON commandes(prospect_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_commandes_statut ON commandes(statut);")

    conn.commit()
    conn.close()


def upsert_prospect(telegram_id: str, nom: str = None, prenom: str = None,
                    telephone: str = None, email: str = None, ville: str = None,
                    langue: str = "fr", source: str = "telegram",
                    statut: str = "nouveau", notes: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM prospects WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()

    if row:
        prospect_id = row["id"]
        fields = []
        values = []
        if nom is not None:
            fields.append("nom = ?"); values.append(nom)
        if prenom is not None:
            fields.append("prenom = ?"); values.append(prenom)
        if telephone is not None:
            fields.append("telephone = ?"); values.append(telephone)
        if email is not None:
            fields.append("email = ?"); values.append(email)
        if ville is not None:
            fields.append("ville = ?"); values.append(ville)
        if langue is not None:
            fields.append("langue = ?"); values.append(langue)
        if statut is not None:
            fields.append("statut = ?"); values.append(statut)
        if notes is not None:
            fields.append("notes = ?"); values.append(notes)
        if fields:
            values.append(prospect_id)
            cur.execute(f"UPDATE prospects SET {', '.join(fields)} WHERE id = ?", values)
    else:
        cur.execute("""
            INSERT INTO prospects (telegram_id, nom, prenom, telephone, email, ville, langue, source, statut, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, nom, prenom, telephone, email, ville, langue, source, statut, notes))
        prospect_id = cur.lastrowid

    conn.commit()
    conn.close()
    return prospect_id


def get_prospect_by_telegram_id(telegram_id: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prospects WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_commande(prospect_id: int, produit_id: str, produit_nom: str,
                    prix_unitaire: float, quantite: int = 1,
                    adresse_livraison: str = None, notes: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    prix_total = prix_unitaire * quantite
    cur.execute("""
        INSERT INTO commandes (prospect_id, produit_id, produit_nom, quantite, prix_unitaire, prix_total, adresse_livraison, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (prospect_id, produit_id, produit_nom, quantite, prix_unitaire, prix_total, adresse_livraison, notes))
    commande_id = cur.lastrowid
    conn.commit()
    conn.close()
    return commande_id


def update_commande_statut(commande_id: int, statut: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE commandes
        SET statut = ?, date_modification = datetime('now','localtime')
        WHERE id = ?
    """, (statut, commande_id))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_commandes_by_prospect(prospect_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM commandes WHERE prospect_id = ? ORDER BY date_commande DESC", (prospect_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def log_interaction(prospect_id: int, type_interaction: str, contenu: str = None) -> None:
    conn = get_connection()
    conn.execute("""
        INSERT INTO interactions (prospect_id, type_interaction, contenu)
        VALUES (?, ?, ?)
    """, (prospect_id, type_interaction, contenu))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM prospects")
    total_prospects = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM commandes")
    total_commandes = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(prix_total), 0) AS ca FROM commandes WHERE statut NOT IN ('annulee')")
    chiffre_affaires = cur.fetchone()["ca"]

    cur.execute("SELECT statut, COUNT(*) AS nb FROM commandes GROUP BY statut")
    commandes_par_statut = {row["statut"]: row["nb"] for row in cur.fetchall()}

    cur.execute("""
        SELECT produit_nom, COUNT(*) AS nb, SUM(prix_total) AS total
        FROM commandes
        WHERE statut NOT IN ('annulee')
        GROUP BY produit_id
        ORDER BY nb DESC
        LIMIT 5
    """)
    top_produits = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT DATE(date_inscription) AS jour, COUNT(*) AS nb
        FROM prospects
        GROUP BY jour
        ORDER BY jour DESC
        LIMIT 7
    """)
    inscriptions_7j = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "total_prospects": total_prospects,
        "total_commandes": total_commandes,
        "chiffre_affaires_tnd": round(chiffre_affaires, 2),
        "commandes_par_statut": commandes_par_statut,
        "top_produits": top_produits,
        "inscriptions_7j": inscriptions_7j,
    }


def get_all_prospects_with_commandes() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.telegram_id, p.nom, p.prenom, p.telephone, p.ville, p.langue,
               p.statut, p.date_inscription,
               COUNT(c.id) AS nb_commandes,
               COALESCE(SUM(c.prix_total), 0) AS total_depense
        FROM prospects p
        LEFT JOIN commandes c ON c.prospect_id = p.id
        GROUP BY p.id
        ORDER BY p.date_inscription DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print(f"[OK] Base de données initialisée : {DB_PATH}")
