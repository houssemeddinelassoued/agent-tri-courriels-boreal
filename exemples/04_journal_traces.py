"""Exemple 4 · Journal des traces (modules 9 et 10 · Monitoring).

Chaque étape du graphe est enregistrée dans traces/traces.jsonl : nœud, horodatage, durée,
statut, sortie et, pour l'extraction, les jetons consommés. On traite les 4 courriels de
démonstration, puis on relit le journal comme le ferait une équipe d'exploitation.

Lancer :  uv run python exemples/04_journal_traces.py
"""

from collections import defaultdict

from boreal_agent.console import FIN, GRAS, GRIS, ROUGE, exiger_ollama, note, titre
from boreal_agent.donnees import charger_courriels_demo
from boreal_agent.extraction import ExtracteurOllama
from boreal_agent.graphe import construire_agent, traiter
from boreal_agent.systemes import SystemesBoreal
from boreal_agent.traces import Traceur

exiger_ollama()
extracteur = ExtracteurOllama()
traceur = Traceur(extracteur=extracteur)
agent = construire_agent(extracteur, SystemesBoreal.depuis_fichier(), traceur=traceur)

for courriel in charger_courriels_demo():
    note(f"Traitement du courriel {courriel.id} · {courriel.objet}")
    traiter(agent, courriel)

titre("Relecture du journal (cette session)")
par_execution = defaultdict(list)
for evenement in traceur.evenements:
    par_execution[(evenement["execution_id"], evenement["courriel_id"])].append(evenement)

for (execution, courriel_id), evenements in par_execution.items():
    total = sum(e["duree_ms"] for e in evenements)
    print(f"\n  {GRAS}Exécution {execution} · courriel {courriel_id} · {total} ms{FIN}")
    for e in evenements:
        barre = "█" * (e["duree_ms"] // 100) or "·"
        jetons = e.get("jetons") or {}
        detail = f"{jetons.get('input_tokens', '?')} → {jetons.get('output_tokens', '?')} jetons" if "jetons" in e else ""
        couleur = ROUGE if e["statut"] != "ok" else ""
        print(f"    {couleur}{e['noeud']:<10}{FIN} {e['duree_ms']:>6} ms {GRIS}{barre}{FIN} {detail}")

note(f"\nJournal complet : {traceur.fichier}")
note("À journaliser en production : entrées, décisions, appels d'outils, coûts, escalades. Pas les secrets.")
