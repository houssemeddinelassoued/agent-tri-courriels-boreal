"""Exemple 1 · Humain dans la boucle (modules 6 et 8).

Le graphe se met en pause (`interrupt`) avant tout remboursement. Son état est sauvegardé
par un checkpointer ; la décision de l'humain le fait repartir (`Command(resume=…)`).
"""

import streamlit as st

import commun
from boreal_agent.donnees import charger_courriels_demo, charger_jeu_de_test
from boreal_agent.graphe import config_execution, construire_agent, nouveau_checkpointer, reprendre, traiter

pret = commun.configurer_page("Humain dans la boucle", "🧑‍⚖️")
st.title("🧑‍⚖️ Exemple 1 · Humain dans la boucle")
st.markdown(
    "Quand l'argent du client est en jeu, l'agent **prépare** (vérification, montant, réponse) mais "
    "n'**exécute** rien : le graphe se met en pause et attend une décision humaine. "
    "Rien n'est remboursé avant l'approbation."
)

# Le graphe et son checkpointer doivent survivre aux rechargements de la page
if "hitl_agent" not in st.session_state:
    st.session_state.hitl_agent = construire_agent(
        commun.extracteur(),
        commun.systemes(),
        humain_dans_la_boucle=True,
        checkpointer=nouveau_checkpointer(),
        traceur=commun.traceur(),
    )
agent = st.session_state.hitl_agent

candidats = [c for c in charger_courriels_demo() if c.id == "B"] + [
    cas.courriel for cas in charger_jeu_de_test() if cas.attendu.action == "validation_humaine" and cas.courriel.id != "T02"
]
par_id = {c.id: c for c in candidats}
choix = par_id[st.selectbox("Courriel de remboursement", par_id, format_func=lambda i: f"{i} · {par_id[i].nom} — {par_id[i].objet}")]
commun.afficher_courriel(choix)

if st.button("▶ Traiter le courriel", type="primary", disabled=not pret):
    config = config_execution()
    with st.spinner("Extraction et vérifications…"):
        etat = traiter(agent, choix, config)
    st.session_state.hitl = {"config": config, "etat": etat, "final": None}

session = st.session_state.get("hitl")
if session:
    etat = session["etat"]
    commun.afficher_resultat(etat)

    if "__interrupt__" in etat and session["final"] is None:
        pause = etat["__interrupt__"][0].value
        instantane = agent.get_state(session["config"])
        st.divider()
        st.subheader("⏸ Le graphe est en pause")
        st.caption(
            f"Prochaine étape sauvegardée : `{instantane.next}` · thread `{session['config']['configurable']['thread_id'][:8]}…` "
            f"· remboursements effectués à ce stade : **{len(commun.systemes().remboursements)}**"
        )
        with st.container(border=True):
            st.markdown(f"### {pause['question']}")
            st.write(pause["resume"])
            st.text(pause["brouillon"])
            par = st.text_input("Validé par", "Chantal Gagné (conseillère)")
            commentaire = st.text_input("Commentaire (en cas de refus)", "")
            col1, col2 = st.columns(2)
            if col1.button("✅ Approuver le remboursement", type="primary", width="stretch"):
                session["final"] = reprendre(agent, session["config"], "approuver", par, commentaire)
                st.rerun()
            if col2.button("❌ Refuser et escalader", width="stretch"):
                session["final"] = reprendre(agent, session["config"], "refuser", par, commentaire)
                st.rerun()

    if session["final"] is not None:
        st.divider()
        st.subheader("▶ Le graphe a repris")
        final = session["final"]
        for action in final.get("actions", [])[-3:]:
            st.markdown(f"- {action}")
        st.success(f"Statut final : **{final['statut']}**")

commun.afficher_systemes()
