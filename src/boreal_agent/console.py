"""Petits utilitaires d'affichage pour les exemples en ligne de commande."""

import sys

from boreal_agent.extraction import verifier_ollama

# La console Windows n'est pas en UTF-8 par défaut : accents et symboles seraient illisibles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GRAS, VERT, JAUNE, ROUGE, BLEU, GRIS, FIN = "\033[1m", "\033[32m", "\033[33m", "\033[31m", "\033[34m", "\033[90m", "\033[0m"

COULEUR_ACTION = {"reponse_auto": VERT, "validation_humaine": JAUNE, "escalade": ROUGE}


def titre(texte: str) -> None:
    print(f"\n{GRAS}{BLEU}═══ {texte} {'═' * max(3, 70 - len(texte))}{FIN}")


def etape(nom: str, texte: str) -> None:
    print(f"  {GRAS}{nom:<11}{FIN} {texte}")


def note(texte: str) -> None:
    print(f"  {GRIS}{texte}{FIN}")


def exiger_ollama() -> None:
    ok, message = verifier_ollama()
    if not ok:
        print(f"{ROUGE}✗ {message}{FIN}")
        sys.exit(1)
    note(f"✓ {message}")


def afficher_etat(etat: dict) -> None:
    """Affiche le résultat d'un traitement, étape par étape."""
    if etat.get("alertes"):
        etape("Lire", f"{ROUGE}passages suspects : {etat['alertes']}{FIN}")
    else:
        etape("Lire", "aucun passage suspect")
    if "extraction" in etat:
        e = etat["extraction"]
        etape("Extraire", f"{e.intention} · commande {e.numero_commande} · {e.montant} $ · {e.sentiment} · urgence {e.urgence}")
        note(f"             résumé : {e.resume}")
    if "decision" in etat:
        d = etat["decision"]
        etape("Décider", f"{COULEUR_ACTION[d.action]}{d.action}{FIN} — {d.motif}")
    for action in etat.get("actions", []):
        etape("Journal", action)
    if etat.get("statut"):
        etape("Statut", f"{GRAS}{etat['statut']}{FIN}")
