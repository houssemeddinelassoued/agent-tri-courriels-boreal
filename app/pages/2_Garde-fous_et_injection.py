"""Exemple 2 · Garde-fous et injection de prompt (module 6, OWASP LLM01 et LLM06)."""

import streamlit as st

import commun
from boreal_agent.agent_naif import CONSIGNE_NAIVE, executer_agent_naif
from boreal_agent.donnees import charger_courriels_demo
from boreal_agent.garde_fous import GardeFouDeclenche
from boreal_agent.graphe import construire_agent, traiter
from boreal_agent.schemas import Courriel

pret = commun.configurer_page("Garde-fous", "🛡️")
st.title("🛡️ Exemple 2 · Garde-fous et injection de prompt")
st.markdown(
    "Pour un agent, **tout texte qu'il lit peut devenir un ordre**… si on le laisse faire. "
    "Le courriel ci-dessous cache une instruction. Modifiez-le librement pour tester d'autres attaques."
)

piege = next(c for c in charger_courriels_demo() if c.id == "D")
corps = st.text_area("Courriel reçu (modifiable)", piege.corps, height=150)
courriel = Courriel(**(piege.model_dump() | {"corps": corps}))

naif, protege = st.columns(2)

with naif:
    st.subheader("❌ Agent naïf")
    st.caption(f"Consigne : « {CONSIGNE_NAIVE} » · outil de crédit **sans plafond**")
    if st.button("Lancer l'agent naïf", disabled=not pret):
        with st.spinner("Le modèle choisit ses outils…"):
            resultat = executer_agent_naif(courriel)
        if resultat["journal"]:
            for ligne in resultat["journal"]:
                st.error(ligne, icon="💸")
            st.markdown("**L'injection a réussi** : le modèle a obéi au texte caché dans le courriel.")
        else:
            st.info(f"Aucun outil appelé cette fois. Réponse : {resultat['texte'][:300]}")
            st.markdown("Il a résisté cette fois-ci… mais **rien ne garantit** qu'il résistera la prochaine fois.")

with protege:
    st.subheader("✅ Agent protégé")
    filtre = st.toggle("Filtre d'entrée activé", value=True, help="Désactivez-le : les règles et le plafond protègent encore")
    st.caption("Le courriel est une **donnée** · la règle fixe le montant · plafond **codé dans l'outil**")
    if st.button("Lancer l'agent protégé", type="primary", disabled=not pret):
        agent = construire_agent(commun.extracteur(), commun.systemes(), traceur=commun.traceur(), filtre_injection=filtre)
        with st.spinner("Lire → Extraire → Décider → Agir…"):
            etat = traiter(agent, courriel)
        commun.afficher_resultat(etat)
        credits = [c["montant"] for c in commun.systemes().credits.values()]
        st.markdown(f"Crédits accordés depuis le début de la session : **{credits or 'aucun'}**")

st.divider()
st.subheader("🔒 Test direct de l'outil `accorder_credit`")
st.markdown("Et si le LLM (ou un pirate) appelait l'outil avec un gros montant ?")
col1, col2 = st.columns([1, 2])
montant = col1.number_input("Montant demandé ($)", min_value=1.0, value=5000.0, step=100.0)
if col2.button("Appeler accorder_credit()"):
    try:
        st.success(commun.systemes().accorder_credit("45812", montant, "test direct", cle=f"test-{montant}"))
    except GardeFouDeclenche as refus:
        st.error(str(refus), icon="🛡️")

st.info("**À retenir** : un prompt n'est pas un contrôle. Les limites vivent dans le code des outils.", icon="💡")
