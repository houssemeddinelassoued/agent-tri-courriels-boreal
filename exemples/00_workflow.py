"""Exemple 0 · Le workflow de base : Lire → Extraire → Décider → Agir (module 8).

Les trois courriels du simulateur du cours, trois issues différentes :
  A. « Où est ma commande #45812 ? »  → réponse automatique + crédit (retard, commande < 500 $)
  B. Facture payée en double          → remboursement préparé, en attente d'un humain
  C. Client en colère                  → escalade avec résumé, priorité haute

Lancer :  uv run python exemples/00_workflow.py
"""

from boreal_agent.console import afficher_etat, exiger_ollama, titre
from boreal_agent.donnees import charger_courriels_demo
from boreal_agent.extraction import ExtracteurOllama
from boreal_agent.graphe import construire_agent, traiter
from boreal_agent.systemes import SystemesBoreal

exiger_ollama()
extracteur = ExtracteurOllama()
systemes = SystemesBoreal.depuis_fichier()
agent = construire_agent(extracteur, systemes)

for courriel in charger_courriels_demo()[:3]:
    titre(f"Courriel {courriel.id} · {courriel.nom} · « {courriel.objet} »")
    afficher_etat(traiter(agent, courriel))

titre("Bilan dans les systèmes de Boréal")
print(f"  Courriels envoyés : {len(systemes.courriels_envoyes)}")
print(f"  Crédits accordés  : {[c['montant'] for c in systemes.credits.values()]}")
print(f"  Billets créés     : {[t['ticket'] + ' (' + t['priorite'] + ')' for t in systemes.tickets]}")
