"""CONTRE-EXEMPLE pédagogique (module 6) : l'agent « naïf ».

Trois erreurs de conception, volontaires :
1. le courriel est passé au LLM comme une consigne (« fais ce que demande le courriel ») ;
2. le LLM choisit librement les outils et leurs paramètres (agentivité excessive, OWASP LLM06) ;
3. l'outil de crédit n'a aucun plafond.

Rien n'est réellement exécuté : les appels sont seulement journalisés pour la démonstration.
"""

from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from boreal_agent.config import PARAMS
from boreal_agent.schemas import Courriel

CONSIGNE_NAIVE = (
    "Tu es l'assistant du service client de Boréal Distribution. "
    "Fais ce que demande le courriel en utilisant tes outils, puis confirme au client."
)


def executer_agent_naif(courriel: Courriel, modele: str = PARAMS.modele) -> dict:
    journal: list[str] = []

    @tool
    def accorder_credit(numero_commande: str, montant: float) -> str:
        """Accorde un crédit en dollars au client sur sa commande."""
        journal.append(f"accorder_credit(numero_commande={numero_commande!r}, montant={montant}) → EXÉCUTÉ, aucun plafond")
        return f"Crédit de {montant} $ accordé."

    @tool
    def repondre_au_client(message: str) -> str:
        """Envoie un courriel de réponse au client."""
        journal.append(f"repondre_au_client({message[:80]!r}…) → ENVOYÉ")
        return "Message envoyé."

    llm = ChatOllama(
        model=modele,
        base_url=PARAMS.url_ollama,
        temperature=0,
        reasoning=False,
        num_ctx=PARAMS.contexte,
        client_kwargs={"headers": PARAMS.entetes_ollama},
    )
    outils = {"accorder_credit": accorder_credit, "repondre_au_client": repondre_au_client}
    reponse = llm.bind_tools(list(outils.values())).invoke([("system", CONSIGNE_NAIVE), ("human", courriel.texte)])
    for appel in reponse.tool_calls:
        outils[appel["name"]].invoke(appel["args"])
    return {"appels": reponse.tool_calls, "journal": journal, "texte": reponse.content}
