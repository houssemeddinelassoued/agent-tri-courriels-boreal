"""Agent de tri des courriels du service client de Boréal Distribution.

Projet de démonstration de la formation Technologia IA134
« Feuille de route pour l'IA agentique ».

Principe (module 8) : le LLM comprend, des règles décident, des outils agissent.
"""

from boreal_agent.graphe import construire_agent, traiter
from boreal_agent.schemas import Commande, Courriel, Decision, Extraction

__all__ = ["Commande", "Courriel", "Decision", "Extraction", "construire_agent", "traiter"]
