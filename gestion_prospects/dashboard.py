#!/usr/bin/env python3
"""
Arvea Nature — Dashboard Terminal
Visualisation des KPI via tabulate
"""
import sys
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from tabulate import tabulate
except ImportError:
    print("[ERREUR] Module 'tabulate' manquant. Installez-le avec : pip install tabulate")
    sys.exit(1)

from gestion_prospects.prospect_manager import (
    init_db, get_stats, get_all_prospects_with_commandes,
    get_commandes_by_prospect, get_connection
)

GREEN = "\033[92m"
BOLD  = "\033[1m"
RESET = "\033[0m"
CYAN  = "\033[96m"
YELLOW = "\033[93m"
RED   = "\033[91m"
MAGENTA = "\033[95m"
DIM   = "\033[2m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"\n{BOLD}{GREEN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           🌿  ARVEA NATURE — DASHBOARD TERMINAL         ║")
    print(f"║                    {DIM}Actualisé : {now}{GREEN}               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")


def print_kpis(stats: dict):
    print(f"{BOLD}{CYAN}📊 INDICATEURS CLÉS DE PERFORMANCE{RESET}")
    print("─" * 58)

    kpi_data = [
        ["👥 Total Prospects",    f"{stats['total_prospects']}",                  "clients potentiels"],
        ["🛒 Total Commandes",    f"{stats['total_commandes']}",                  "commandes enregistrées"],
        ["💰 Chiffre d'Affaires", f"{stats['chiffre_affaires_tnd']:.2f} TND",    "hors annulées"],
    ]
    print(tabulate(kpi_data, headers=["Indicateur", "Valeur", "Note"],
                   tablefmt="rounded_outline", colalign=("left", "right", "left")))
    print()


def print_commandes_par_statut(stats: dict):
    print(f"{BOLD}{CYAN}📦 COMMANDES PAR STATUT{RESET}")
    print("─" * 40)

    statuts = stats.get("commandes_par_statut", {})
    if not statuts:
        print(f"{DIM}  Aucune commande enregistrée.{RESET}\n")
        return

    statut_icons = {
        "en_attente":    "⏳",
        "confirmee":     "✅",
        "en_preparation": "🔧",
        "expediee":      "🚚",
        "livree":        "📬",
        "annulee":       "❌",
    }
    rows = []
    total = sum(statuts.values())
    for statut, nb in sorted(statuts.items()):
        icon = statut_icons.get(statut, "•")
        label = statut.replace("_", " ").title()
        pct = (nb / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        rows.append([f"{icon} {label}", nb, f"{pct:.1f}%", bar])

    print(tabulate(rows, headers=["Statut", "Nb", "%", "Répartition"],
                   tablefmt="rounded_outline", colalign=("left", "right", "right", "left")))
    print()


def print_top_produits(stats: dict):
    print(f"{BOLD}{CYAN}🏆 TOP PRODUITS (hors annulées){RESET}")
    print("─" * 56)

    top = stats.get("top_produits", [])
    if not top:
        print(f"{DIM}  Aucune vente enregistrée.{RESET}\n")
        return

    rows = []
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, p in enumerate(top):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        rows.append([
            medal,
            p["produit_nom"],
            p["nb"],
            f"{p['total']:.2f} TND"
        ])

    print(tabulate(rows, headers=["#", "Produit", "Ventes", "CA (TND)"],
                   tablefmt="rounded_outline", colalign=("left", "left", "right", "right")))
    print()


def print_inscriptions_recentes(stats: dict):
    print(f"{BOLD}{CYAN}📅 INSCRIPTIONS (7 DERNIERS JOURS){RESET}")
    print("─" * 44)

    insc = stats.get("inscriptions_7j", [])
    if not insc:
        print(f"{DIM}  Aucune inscription récente.{RESET}\n")
        return

    rows = [[r["jour"], r["nb"]] for r in insc]
    print(tabulate(rows, headers=["Date", "Nouveaux prospects"],
                   tablefmt="rounded_outline", colalign=("left", "right")))
    print()


def print_prospects_list(limit: int = 10):
    print(f"{BOLD}{CYAN}👥 DERNIERS PROSPECTS ({limit} entrées){RESET}")
    print("─" * 70)

    prospects = get_all_prospects_with_commandes()
    if not prospects:
        print(f"{DIM}  Aucun prospect enregistré.{RESET}\n")
        return

    rows = []
    for p in prospects[:limit]:
        nom_complet = f"{p.get('prenom') or ''} {p.get('nom') or ''}".strip() or "—"
        tel = p.get("telephone") or "—"
        ville = p.get("ville") or "—"
        lang_flag = "🇫🇷" if p.get("langue") == "fr" else "🇹🇳"
        statut = p.get("statut", "—")
        nb_cmd = p.get("nb_commandes", 0)
        total = f"{p.get('total_depense', 0):.0f} TND"
        rows.append([p["id"], nom_complet, tel, ville, lang_flag, statut, nb_cmd, total])

    print(tabulate(rows,
                   headers=["ID", "Nom Complet", "Téléphone", "Ville", "🌐", "Statut", "Cmd", "Dépensé"],
                   tablefmt="rounded_outline",
                   colalign=("right", "left", "left", "left", "center", "left", "right", "right")))
    print()


def print_commandes_recentes(limit: int = 10):
    print(f"{BOLD}{CYAN}🛒 DERNIÈRES COMMANDES ({limit} entrées){RESET}")
    print("─" * 72)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.date_commande, p.nom, p.prenom, c.produit_nom,
               c.quantite, c.prix_total, c.statut, c.adresse_livraison
        FROM commandes c
        LEFT JOIN prospects p ON p.id = c.prospect_id
        ORDER BY c.date_commande DESC
        LIMIT ?
    """, (limit,))
    rows_raw = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not rows_raw:
        print(f"{DIM}  Aucune commande enregistrée.{RESET}\n")
        return

    statut_colors = {
        "en_attente": YELLOW, "confirmee": GREEN, "livree": GREEN,
        "annulee": RED, "expediee": CYAN, "en_preparation": MAGENTA
    }

    rows = []
    for r in rows_raw:
        nom = f"{r.get('prenom') or ''} {r.get('nom') or ''}".strip() or "—"
        date_fmt = r["date_commande"][:16] if r["date_commande"] else "—"
        statut = r["statut"] or "—"
        ref = f"CMD-{r['id']:05d}"
        rows.append([ref, date_fmt, nom, r["produit_nom"], r["quantite"],
                     f"{r['prix_total']:.2f}", statut])

    print(tabulate(rows,
                   headers=["Réf.", "Date", "Client", "Produit", "Qté", "Total TND", "Statut"],
                   tablefmt="rounded_outline",
                   colalign=("left", "left", "left", "left", "right", "right", "left")))
    print()


def print_menu():
    print(f"{BOLD}⚙️  ACTIONS DISPONIBLES{RESET}")
    print("─" * 40)
    print("  [1] Actualiser le dashboard")
    print("  [2] Voir tous les prospects")
    print("  [3] Voir toutes les commandes")
    print("  [4] Envoyer rapport email")
    print("  [0] Quitter")
    print()


def run_dashboard():
    init_db()
    while True:
        clear_screen()
        print_header()

        stats = get_stats()
        print_kpis(stats)
        print_commandes_par_statut(stats)
        print_top_produits(stats)
        print_inscriptions_recentes(stats)
        print_prospects_list(limit=8)
        print_commandes_recentes(limit=8)
        print_menu()

        try:
            choice = input(f"{BOLD}Votre choix : {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GREEN}Dashboard fermé. À bientôt ! 🌿{RESET}\n")
            break

        if choice == "0":
            print(f"\n{GREEN}Dashboard fermé. À bientôt ! 🌿{RESET}\n")
            break

        elif choice == "1":
            continue

        elif choice == "2":
            clear_screen()
            print_header()
            all_p = get_all_prospects_with_commandes()
            if all_p:
                rows = []
                for p in all_p:
                    rows.append([
                        p["id"],
                        f"{p.get('prenom') or ''} {p.get('nom') or ''}".strip() or "—",
                        p.get("telephone") or "—",
                        p.get("ville") or "—",
                        p.get("langue") or "—",
                        p.get("statut") or "—",
                        p.get("nb_commandes", 0),
                        f"{p.get('total_depense', 0):.2f} TND",
                        (p.get("date_inscription") or "—")[:10],
                    ])
                print(tabulate(rows,
                               headers=["ID", "Nom", "Tél", "Ville", "Lang", "Statut", "Cmd", "Total", "Inscription"],
                               tablefmt="rounded_outline"))
            else:
                print("Aucun prospect.")
            input(f"\n{DIM}Appuyez sur Entrée pour revenir...{RESET}")

        elif choice == "3":
            clear_screen()
            print_header()
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT c.id, c.date_commande, p.nom, p.prenom,
                       c.produit_nom, c.quantite, c.prix_total, c.statut, c.adresse_livraison
                FROM commandes c
                LEFT JOIN prospects p ON p.id = c.prospect_id
                ORDER BY c.date_commande DESC
            """)
            all_c = [dict(r) for r in cur.fetchall()]
            conn.close()

            if all_c:
                rows = []
                for r in all_c:
                    nom = f"{r.get('prenom') or ''} {r.get('nom') or ''}".strip() or "—"
                    rows.append([
                        f"CMD-{r['id']:05d}",
                        (r["date_commande"] or "—")[:16],
                        nom,
                        r["produit_nom"],
                        r["quantite"],
                        f"{r['prix_total']:.2f}",
                        r["statut"],
                    ])
                print(tabulate(rows,
                               headers=["Réf.", "Date", "Client", "Produit", "Qté", "Total TND", "Statut"],
                               tablefmt="rounded_outline"))
            else:
                print("Aucune commande.")
            input(f"\n{DIM}Appuyez sur Entrée pour revenir...{RESET}")

        elif choice == "4":
            try:
                from integration_gmail.send_email import send_rapport_journalier
                print(f"{YELLOW}Envoi du rapport en cours...{RESET}")
                ok = send_rapport_journalier(get_stats())
                if ok:
                    print(f"{GREEN}✅ Rapport envoyé avec succès !{RESET}")
                else:
                    print(f"{RED}❌ Échec de l'envoi. Vérifiez la configuration Gmail dans config/.env{RESET}")
            except Exception as e:
                print(f"{RED}❌ Erreur : {e}{RESET}")
            input(f"\n{DIM}Appuyez sur Entrée pour revenir...{RESET}")

        else:
            print(f"{RED}Choix invalide.{RESET}")
            import time
            time.sleep(0.8)


if __name__ == "__main__":
    run_dashboard()
