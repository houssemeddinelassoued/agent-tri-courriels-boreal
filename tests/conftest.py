"""Outils de test : un faux extracteur déterministe remplace le LLM.

Les tests vérifient le graphe, les règles et les garde-fous sans Ollama.
"""

import pytest

from boreal_agent.donnees import charger_courriels_demo
from boreal_agent.schemas import Courriel, Extraction
from boreal_agent.systemes import SystemesBoreal

EXTRACTIONS = {
    "A": Extraction(intention="suivi", numero_commande="45812", montant=None, sentiment="neutre", urgence="normale",
                    resume="Le client demande où en est sa commande 45812."),
    "B": Extraction(intention="remboursement", numero_commande="47230", montant=249.5, sentiment="neutre",
                    urgence="normale", resume="La cliente a été débitée deux fois et demande un remboursement."),
    "C": Extraction(intention="retard_livraison", numero_commande="48001", montant=None, sentiment="irrite",
                    urgence="elevee", resume="Le client signale un 3e retard et menace d'annuler."),
    "D": Extraction(intention="retard_livraison", numero_commande="45812", montant=5000, sentiment="neutre",
                    urgence="normale", resume="Le client signale un retard et réclame un crédit."),
}


class FauxExtracteur:
    def __init__(self, extractions: dict[str, Extraction]):
        self.extractions = extractions
        self.dernier_usage = {"input_tokens": 0, "output_tokens": 0}

    def __call__(self, courriel: Courriel) -> Extraction:
        return self.extractions[courriel.id]


@pytest.fixture
def extracteur() -> FauxExtracteur:
    return FauxExtracteur(EXTRACTIONS)


@pytest.fixture
def systemes() -> SystemesBoreal:
    return SystemesBoreal.depuis_fichier()


@pytest.fixture
def courriels() -> dict[str, Courriel]:
    return {c.id: c for c in charger_courriels_demo()}
