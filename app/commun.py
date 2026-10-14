"""Éléments partagés par les pages Streamlit."""

import streamlit as st

from boreal_agent.extraction import ExtracteurOllama, verifier_ollama
from boreal_agent.schemas import Courriel, dollars
from boreal_agent.systemes import SystemesBoreal
from boreal_agent.traces import Traceur

COULEURS = {"reponse_auto": "green", "validation_humaine": "orange", "escalade": "red"}
LIBELLES = {"reponse_auto": "Réponse automatique", "validation_humaine": "Validation humaine", "escalade": "Escalade"}


def configurer_page(titre: str, icone: str) -> bool:
    """En-tête commun ; renvoie False (et l'affiche) si Ollama n'est pas prêt."""
    st.set_page_config(page_title=f"{titre} · Agent Boréal", page_icon=icone, layout="wide")
    ok, message = verifier_ollama()
    with st.sidebar:
        (st.success if ok else st.error)(message, icon="✅" if ok else "⚠️")
        st.caption(
            "Formation Technologia **IA134**  \nFeuille de route pour l'IA agentique  \n"
            "LangGraph · Ollama · données fictives"
        )
        if st.button("Réinitialiser les systèmes Boréal", help="Vide les courriels envoyés, crédits et billets"):
            for cle in ("systemes", "hitl_agent", "hitl", "evaluation"):
                st.session_state.pop(cle, None)
            st.rerun()
    return ok


@st.cache_resource(show_spinner="Connexion au modèle local…")
def extracteur() -> ExtracteurOllama:
    return ExtracteurOllama()


@st.cache_resource
def traceur() -> Traceur:
    return Traceur(extracteur=extracteur())


def systemes() -> SystemesBoreal:
    """Les faux systèmes de Boréal, propres à chaque session du navigateur."""
    if "systemes" not in st.session_state:
        st.session_state.systemes = SystemesBoreal.depuis_fichier()
    return st.session_state.systemes


def afficher_courriel(courriel: Courriel) -> None:
    with st.container(border=True):
        st.caption(f"**De :** {courriel.nom} &lt;{courriel.expediteur}&gt;")
        st.markdown(f"**{courriel.objet}**")
        st.text(courriel.corps)


def schema_graphe(chemin: list[str] | None = None) -> str:
    """Le graphe en langage DOT ; les étapes parcourues sont mises en évidence."""
    chemin = chemin or []

    def noeud(nom: str, libelle: str) -> str:
        actif = nom in chemin
        style = 'fillcolor="#1F78C1", fontcolor="white"' if actif else 'fillcolor="#EAF0F4", fontcolor="#2B2F33"'
        return f'{nom} [label="{libelle}", {style}];'

    lignes = [
        "digraph G {",
        'rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", fontname="Helvetica", color="#93C1E8"];',
        'edge [color="#77818A", fontname="Helvetica", fontsize=10];',
        noeud("lire", "1 · Lire\n(filtre d'entrée)"),
        noeud("extraire", "2 · Extraire\n(LLM → JSON)"),
        noeud("consulter", "3 · Consulter\n(ERP)"),
        noeud("decider", "4 · Décider\n(règles codées)"),
        noeud("repondre", "Répondre\n(+ crédit)"),
        noeud("valider", "Validation\nhumaine"),
        noeud("rembourser", "Rembourser"),
        noeud("escalader", "Escalader\n(billet)"),
        "lire -> extraire -> consulter -> decider;",
        'decider -> repondre [label="réponse auto"];',
        'decider -> valider [label="argent en jeu"];',
        'decider -> escalader [label="sinon"];',
        'valider -> rembourser [label="approuvé"];',
        'valider -> escalader [label="refusé"];',
        "}",
    ]
    return "\n".join(lignes)


def afficher_resultat(etat: dict) -> None:
    """Extraction, décision et actions d'un traitement terminé (ou en pause)."""
    if etat.get("alertes"):
        st.error(f"**Filtre d'entrée** : passages suspects → {', '.join(etat['alertes'])}", icon="🛡️")
    col1, col2 = st.columns(2)
    if "extraction" in etat:
        with col1:
            st.markdown("**2 · Extraction (sortie structurée du LLM)**")
            st.json(etat["extraction"].model_dump())
    with col2:
        commande = etat.get("commande")
        st.markdown("**3 · Commande dans l'ERP**")
        if commande:
            st.write(
                f"{commande.numero} · {commande.produit} · {dollars(commande.total)} · {commande.statut}"
                + (f" · **retard {commande.retard_jours} j**" if commande.retard_jours else "")
            )
        else:
            st.write("Introuvable ou numéro absent")
        if "decision" in etat:
            d = etat["decision"]
            st.markdown("**4 · Décision (règle métier)**")
            st.markdown(f":{COULEURS[d.action]}[**{LIBELLES[d.action]}**] — {d.motif}")
            if d.brouillon:
                with st.expander("Réponse préparée (gabarit approuvé)"):
                    st.text(d.brouillon)
    st.markdown("**Journal des actions**")
    for action in etat.get("actions", []):
        st.markdown(f"- {action}")
    if etat.get("statut"):
        st.info(f"Statut final : **{etat['statut']}**")


def afficher_systemes() -> None:
    s = systemes()
    with st.expander(
        f"État des systèmes Boréal · {len(s.courriels_envoyes)} courriel(s) · {len(s.credits)} crédit(s) · "
        f"{len(s.remboursements)} remboursement(s) · {len(s.tickets)} billet(s)"
    ):
        st.write("**Courriels envoyés**", s.courriels_envoyes or "aucun")
        st.write("**Crédits**", list(s.credits.values()) or "aucun")
        st.write("**Remboursements**", s.remboursements or "aucun")
        st.write("**Billets d'escalade**", s.tickets or "aucun")

