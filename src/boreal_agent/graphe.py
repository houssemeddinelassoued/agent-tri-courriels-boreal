"""Le graphe LangGraph de l'agent : Lire → Extraire → Consulter → Décider → Agir.

                          ┌─ reponse_auto ──────► repondre ──────────────┐
  lire → extraire → consulter → decider ─┤                                     ├─► FIN
                          ├─ validation_humaine ► valider ─► rembourser ─┤
                          │                          └─ refus ─┐         │
                          └─ escalade ──────────► escalader ◄──┘─────────┘

Le chemin est fixé par le code (workflow), pas par le LLM : c'est le choix « commencer simple »
du module 1. Le LLM n'intervient qu'à l'étape « extraire ».
"""

import operator
import uuid
from typing import Annotated, Any, Callable, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from boreal_agent.extraction import Extracteur
from boreal_agent.garde_fous import GardeFouDeclenche, detecter_injection
from boreal_agent.regles import decider
from boreal_agent.schemas import Commande, Courriel, Decision, Extraction, dollars
from boreal_agent.systemes import SystemesBoreal
from boreal_agent.traces import Traceur


class EtatAgent(TypedDict, total=False):
    execution_id: str
    courriel: Courriel
    alertes: list[str]
    extraction: Extraction
    commande: Commande | None
    decision: Decision
    validation: dict
    actions: Annotated[list[str], operator.add]  # journal des actions, cumulé d'étape en étape
    statut: str


def construire_agent(
    extracteur: Extracteur,
    systemes: SystemesBoreal,
    *,
    humain_dans_la_boucle: bool = False,
    checkpointer: Any = None,
    traceur: Traceur | None = None,
    filtre_injection: bool = True,
):
    """Assemble et compile le graphe.

    humain_dans_la_boucle : si vrai, le graphe se met en pause avant tout remboursement
    (`interrupt`) et attend la décision d'un humain. Exige un `checkpointer` pour reprendre.
    filtre_injection : désactivable pour la démonstration ; les règles et le plafond des
    outils protègent quand même.
    """

    def lire(etat: EtatAgent) -> dict:
        if not filtre_injection:
            return {"alertes": [], "actions": ["Filtre d'entrée : désactivé"]}
        alertes = detecter_injection(etat["courriel"].texte)
        note = f"Filtre d'entrée : {len(alertes)} passage(s) suspect(s)" if alertes else "Filtre d'entrée : RAS"
        return {"alertes": alertes, "actions": [note]}

    def extraire(etat: EtatAgent) -> dict:
        return {"extraction": extracteur(etat["courriel"])}

    def consulter(etat: EtatAgent) -> dict:
        numero = etat["extraction"].numero_commande
        commande = systemes.consulter_commande(numero)
        note = f"ERP : commande {commande.numero} trouvée" if commande else f"ERP : commande « {numero} » introuvable"
        return {"commande": commande, "actions": [note]}

    def decider_(etat: EtatAgent) -> dict:
        decision = decider(etat["extraction"], etat.get("commande"), etat.get("alertes", []), etat["courriel"])
        return {"decision": decision}

    def repondre(etat: EtatAgent) -> dict:
        courriel, decision, commande = etat["courriel"], etat["decision"], etat["commande"]
        actions = []
        if decision.credit:
            try:
                actions.append(
                    systemes.accorder_credit(commande.numero, decision.credit, "retard", cle=f"credit-{courriel.id}")
                )
            except GardeFouDeclenche as refus:
                escalade = _escalader(etat, str(refus))
                return {"statut": escalade["statut"], "actions": [str(refus), *escalade["actions"]]}
        actions.append(systemes.envoyer_courriel(courriel.expediteur, f"RE: {courriel.objet}", decision.brouillon))
        return {"actions": actions, "statut": "traite_automatiquement"}

    def valider(etat: EtatAgent) -> dict:
        if not humain_dans_la_boucle:
            return {"validation": {"decision": "en_attente"}, "statut": "en_attente_validation"}
        decision, commande = etat["decision"], etat["commande"]
        # Pause : le graphe est sauvegardé et attend Command(resume={...})
        reponse = interrupt(
            {
                "question": f"Rembourser {dollars(decision.montant_remboursement)} sur la commande {commande.numero} ?",
                "resume": etat["extraction"].resume,
                "brouillon": decision.brouillon,
            }
        )
        return {"validation": reponse, "actions": [f"Validation humaine : {reponse.get('decision')} par {reponse.get('par')}"]}

    def rembourser(etat: EtatAgent) -> dict:
        courriel, decision, commande = etat["courriel"], etat["decision"], etat["commande"]
        actions = [
            systemes.rembourser(commande.numero, decision.montant_remboursement, approuve_par=etat["validation"]["par"]),
            systemes.envoyer_courriel(courriel.expediteur, f"RE: {courriel.objet}", decision.brouillon),
        ]
        return {"actions": actions, "statut": "rembourse_apres_validation"}

    def _escalader(etat: EtatAgent, motif: str) -> dict:
        extraction = etat["extraction"]
        priorite = etat["decision"].priorite if "decision" in etat else "normale"
        ticket = systemes.creer_ticket(etat["courriel"].id, extraction.resume, motif, priorite)
        return {"statut": "escalade", "actions": [ticket]}

    def escalader(etat: EtatAgent) -> dict:
        motif = etat["decision"].motif
        if etat.get("validation", {}).get("decision") == "refuser":
            motif = f"Refusé par {etat['validation'].get('par')} : {etat['validation'].get('commentaire') or 'sans commentaire'}"
        return _escalader(etat, motif)

    noeuds: dict[str, Callable] = {
        "lire": lire,
        "extraire": extraire,
        "consulter": consulter,
        "decider": decider_,
        "repondre": repondre,
        "valider": valider,
        "rembourser": rembourser,
        "escalader": escalader,
    }
    graphe = StateGraph(EtatAgent)
    for nom, fonction in noeuds.items():
        graphe.add_node(nom, traceur.envelopper(nom, fonction) if traceur else fonction)

    graphe.add_edge(START, "lire")
    graphe.add_edge("lire", "extraire")
    graphe.add_edge("extraire", "consulter")
    graphe.add_edge("consulter", "decider")
    graphe.add_conditional_edges(
        "decider",
        lambda etat: etat["decision"].action,
        {"reponse_auto": "repondre", "validation_humaine": "valider", "escalade": "escalader"},
    )
    graphe.add_conditional_edges(
        "valider",
        lambda etat: etat["validation"].get("decision", "en_attente"),
        {"approuver": "rembourser", "refuser": "escalader", "en_attente": END},
    )
    for fin in ("repondre", "rembourser", "escalader"):
        graphe.add_edge(fin, END)

    return graphe.compile(checkpointer=checkpointer)


def nouveau_checkpointer() -> InMemorySaver:
    """Mémoire des graphes en pause. Nos types sont déclarés explicitement : LangGraph refuse
    de restaurer des classes inconnues d'une sauvegarde (protection contre le code injecté)."""
    types = [("boreal_agent.schemas", nom) for nom in ("Courriel", "Extraction", "Commande", "Decision")]
    return InMemorySaver(serde=JsonPlusSerializer(allowed_msgpack_modules=types))


def config_execution(thread_id: str | None = None) -> dict:
    """Configuration LangGraph : le thread_id identifie une conversation sauvegardée."""
    return {"configurable": {"thread_id": thread_id or uuid.uuid4().hex}}


def etat_initial(courriel: Courriel) -> EtatAgent:
    return {"execution_id": uuid.uuid4().hex[:8], "courriel": courriel, "actions": []}


def traiter(agent, courriel: Courriel, config: dict | None = None) -> dict:
    """Traite un courriel de bout en bout et renvoie l'état final (ou en pause)."""
    return agent.invoke(etat_initial(courriel), config or config_execution())


def reprendre(agent, config: dict, decision: str, par: str, commentaire: str = "") -> dict:
    """Reprend un graphe en pause avec la décision de l'humain (« approuver » ou « refuser »)."""
    return agent.invoke(Command(resume={"decision": decision, "par": par, "commentaire": commentaire}), config)
