"""Évaluation sur le jeu de test « doré » et calcul des KPI (module 10).

Quatre familles de KPI : qualité (exactitude), efficacité (automatisation, latence),
risque (erreurs graves : automatiser ce qui devait aller à un humain) et charge humaine.
Un seul chiffre raconte toujours une demi-vérité : on les lit ensemble.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from pydantic import BaseModel

from boreal_agent.config import PARAMS
from boreal_agent.donnees import CasTest
from boreal_agent.extraction import Extracteur
from boreal_agent.graphe import construire_agent, traiter
from boreal_agent.systemes import SystemesBoreal


class ResultatCas(BaseModel):
    id: str
    objet: str
    intention_attendue: str
    intention_obtenue: str
    numero_attendu: str | None
    numero_obtenu: str | None
    action_attendue: str
    action_obtenue: str
    ok_intention: bool
    ok_numero: bool
    ok_action: bool
    erreur_grave: bool
    duree_s: float


def evaluer(
    extracteur: Extracteur,
    jeu: list[CasTest],
    progression: Callable[[int, int, str], None] | None = None,
) -> tuple[list[ResultatCas], dict]:
    resultats = []
    for i, cas in enumerate(jeu, start=1):
        if progression:
            progression(i, len(jeu), cas.courriel.objet)
        # Systèmes neufs à chaque cas : aucun effet de bord d'un cas sur l'autre
        agent = construire_agent(extracteur, SystemesBoreal.depuis_fichier())
        debut = time.perf_counter()
        etat = traiter(agent, cas.courriel)
        duree = time.perf_counter() - debut
        extraction, decision, attendu = etat["extraction"], etat["decision"], cas.attendu
        resultats.append(
            ResultatCas(
                id=cas.courriel.id,
                objet=cas.courriel.objet,
                intention_attendue=" / ".join(attendu.intentions),
                intention_obtenue=extraction.intention,
                numero_attendu=attendu.numero_commande,
                numero_obtenu=extraction.numero_commande,
                action_attendue=attendu.action,
                action_obtenue=decision.action,
                ok_intention=extraction.intention in attendu.intentions,
                ok_numero=extraction.numero_commande == attendu.numero_commande,
                ok_action=decision.action == attendu.action,
                # Le pire cas : l'agent agit seul alors qu'un humain devait intervenir
                erreur_grave=decision.action == "reponse_auto" and attendu.action != "reponse_auto",
                duree_s=round(duree, 2),
            )
        )
    return resultats, calculer_kpis(resultats)


def calculer_kpis(resultats: list[ResultatCas]) -> dict:
    n = len(resultats) or 1

    def taux(condition) -> float:
        return round(100 * sum(1 for r in resultats if condition(r)) / n, 1)

    return {
        "nb_cas": len(resultats),
        "exactitude_intention": taux(lambda r: r.ok_intention),
        "exactitude_numero": taux(lambda r: r.ok_numero),
        "exactitude_decision": taux(lambda r: r.ok_action),
        "taux_automatisation": taux(lambda r: r.action_obtenue == "reponse_auto"),
        "taux_validation_humaine": taux(lambda r: r.action_obtenue == "validation_humaine"),
        "taux_escalade": taux(lambda r: r.action_obtenue == "escalade"),
        "erreurs_graves": sum(1 for r in resultats if r.erreur_grave),
        "latence_moyenne_s": round(sum(r.duree_s for r in resultats) / n, 2),
    }


def sauvegarder_rapport(resultats: list[ResultatCas], kpis: dict, modele: str, dossier: Path | None = None) -> Path:
    dossier = dossier or PARAMS.dossier_rapports
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"evaluation-{datetime.now():%Y%m%d-%H%M%S}.json"
    rapport = {"modele": modele, "date": datetime.now().isoformat(timespec="seconds"), "kpis": kpis,
               "resultats": [r.model_dump() for r in resultats]}
    chemin.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    return chemin
