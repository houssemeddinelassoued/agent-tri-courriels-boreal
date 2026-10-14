"""Chargement des données fictives de Boréal (courriels de démonstration et jeu de test)."""

import json

from pydantic import BaseModel

from boreal_agent.config import PARAMS
from boreal_agent.schemas import Courriel, Intention, TypeAction


class Attendu(BaseModel):
    intentions: list[Intention]  # plusieurs réponses acceptables quand la frontière est floue
    numero_commande: str | None
    action: TypeAction


class CasTest(BaseModel):
    courriel: Courriel
    attendu: Attendu


def _lire(nom: str) -> list:
    return json.loads((PARAMS.dossier_donnees / nom).read_text(encoding="utf-8"))


def charger_courriels_demo() -> list[Courriel]:
    """Les 3 courriels du simulateur du module 8, plus le courriel piégé du module 6."""
    return [Courriel(**c) for c in _lire("courriels_demo.json")]


def charger_jeu_de_test() -> list[CasTest]:
    """Le jeu de test « doré » : 12 courriels avec la réponse attendue (module 10)."""
    return [CasTest(**c) for c in _lire("jeu_de_test.json")]
