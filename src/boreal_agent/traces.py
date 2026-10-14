"""Journal des traces (modules 9 et 10 · Monitoring).

Chaque étape du graphe est enregistrée : quoi, quand, combien de temps, avec quel résultat.
Les traces vont dans `traces/traces.jsonl` (une ligne JSON par étape), lisibles par l'interface
et par n'importe quel outil d'analyse. En production, on brancherait LangSmith, Langfuse ou
OpenTelemetry au même endroit.
"""

import json
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from langgraph.errors import GraphInterrupt
from pydantic_core import to_jsonable_python

from boreal_agent.config import PARAMS


class Traceur:
    def __init__(self, fichier: Path | None = None, extracteur: Any = None):
        self.fichier = fichier or PARAMS.dossier_traces / "traces.jsonl"
        self.extracteur = extracteur  # pour relever les jetons consommés à l'étape « extraire »
        self.evenements: list[dict] = []

    def envelopper(self, nom: str, fonction: Callable[[dict], dict]) -> Callable[[dict], dict]:
        @wraps(fonction)
        def noeud_trace(etat: dict) -> dict:
            debut = time.perf_counter()
            evenement = {
                "execution_id": etat.get("execution_id", "?"),
                "courriel_id": etat["courriel"].id if "courriel" in etat else "?",
                "noeud": nom,
                "horodatage": datetime.now().isoformat(timespec="seconds"),
            }
            try:
                sortie = fonction(etat)
            except GraphInterrupt:
                # Pause « humain dans la boucle » : ce n'est pas une erreur
                self._ecrire(evenement | {"statut": "pause", "duree_ms": _ms(debut), "sortie": "en attente d'un humain"})
                raise
            except Exception as erreur:
                self._ecrire(evenement | {"statut": "erreur", "duree_ms": _ms(debut), "sortie": repr(erreur)})
                raise
            evenement |= {"statut": "ok", "duree_ms": _ms(debut), "sortie": to_jsonable_python(sortie)}
            if nom == "extraire" and self.extracteur is not None:
                evenement["jetons"] = getattr(self.extracteur, "dernier_usage", {})
            self._ecrire(evenement)
            return sortie

        return noeud_trace

    def _ecrire(self, evenement: dict) -> None:
        self.evenements.append(evenement)
        self.fichier.parent.mkdir(parents=True, exist_ok=True)
        with self.fichier.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evenement, ensure_ascii=False) + "\n")


def lire_traces(fichier: Path | None = None) -> list[dict]:
    fichier = fichier or PARAMS.dossier_traces / "traces.jsonl"
    if not fichier.exists():
        return []
    return [json.loads(ligne) for ligne in fichier.read_text(encoding="utf-8").splitlines() if ligne.strip()]


def _ms(debut: float) -> int:
    return round((time.perf_counter() - debut) * 1000)
