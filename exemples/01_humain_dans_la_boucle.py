"""Exemple 1 · Humain dans la boucle (modules 6 et 8).

Le courriel B demande un remboursement. L'agent prépare tout (vérification, montant, réponse),
puis le graphe se MET EN PAUSE (`interrupt`) : rien n'est remboursé tant qu'un humain n'a pas
approuvé. L'état est sauvegardé par le checkpointer ; la reprise se fait avec `Command(resume=…)`.

Lancer :  uv run python exemples/01_humain_dans_la_boucle.py
          uv run python exemples/01_humain_dans_la_boucle.py --decision refuser   (sans question)
"""

import argparse

from boreal_agent.console import GRAS, FIN, JAUNE, afficher_etat, exiger_ollama, note, titre
from boreal_agent.donnees import charger_courriels_demo
from boreal_agent.extraction import ExtracteurOllama
from boreal_agent.graphe import config_execution, construire_agent, nouveau_checkpointer, reprendre, traiter
from boreal_agent.systemes import SystemesBoreal

parser = argparse.ArgumentParser()
parser.add_argument("--decision", choices=["approuver", "refuser"], help="répondre sans question interactive")
args = parser.parse_args()

exiger_ollama()
systemes = SystemesBoreal.depuis_fichier()
agent = construire_agent(
    ExtracteurOllama(), systemes, humain_dans_la_boucle=True, checkpointer=nouveau_checkpointer()
)
courriel = next(c for c in charger_courriels_demo() if c.id == "B")
config = config_execution()  # le thread_id permet de retrouver le graphe en pause

titre(f"Courriel {courriel.id} · {courriel.nom} · « {courriel.objet} »")
etat = traiter(agent, courriel, config)
afficher_etat(etat)

pause = etat["__interrupt__"][0].value
titre("⏸  Le graphe est en pause : validation humaine requise")
print(f"  {GRAS}{pause['question']}{FIN}")
note(f"Résumé : {pause['resume']}")
print(f"\n  {JAUNE}Brouillon de réponse préparé par l'agent :{FIN}")
for ligne in pause["brouillon"].splitlines():
    print(f"    │ {ligne}")
print(f"\n  Remboursements effectués à ce stade : {systemes.remboursements}  ← rien tant que l'humain n'a pas validé")

decision = args.decision
while decision not in ("approuver", "refuser"):
    decision = {"a": "approuver", "r": "refuser"}.get(input("\n  Votre décision ? [a]pprouver / [r]efuser : ").strip().lower()[:1], "")
commentaire = "" if decision == "approuver" else "Montant à confirmer avec le relevé bancaire"

titre(f"▶  Reprise du graphe : {decision}")
etat = reprendre(agent, config, decision, par="Chantal Gagné (conseillère)", commentaire=commentaire)
afficher_etat(etat)
print(f"\n  Remboursements : {systemes.remboursements}")
print(f"  Billets        : {systemes.tickets}")
