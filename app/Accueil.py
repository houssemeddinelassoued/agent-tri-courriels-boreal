"""Page d'accueil : le workflow complet, étape par étape (module 8).

Lancer :  uv run streamlit run app/Accueil.py
"""

import streamlit as st

import commun
from boreal_agent.donnees import charger_courriels_demo
from boreal_agent.graphe import config_execution, construire_agent, etat_initial
from boreal_agent.schemas import Courriel

pret = commun.configurer_page("Workflow", "📬")

st.title("📬 Agent de tri des courriels · Boréal Distribution")
st.markdown(
    "Le service client reçoit **5 000 courriels par mois**. L'agent lit chaque courriel, en extrait les "
    "informations utiles, applique la règle de Boréal, puis agit : **le LLM comprend, des règles décident, "
    "des outils agissent.**"
)

zone_schema = st.empty()
zone_schema.graphviz_chart(commun.schema_graphe(), width="stretch")

courriels = {f"{c.id} · {c.nom} — {c.objet}": c for c in charger_courriels_demo()}
choix = st.radio("Courriel à traiter", [*courriels, "✍️ Écrire mon propre courriel"], horizontal=False)

if choix in courriels:
    courriel = courriels[choix]
    commun.afficher_courriel(courriel)
else:
    with st.form("libre"):
        nom = st.text_input("Nom du client", "Client test")
        objet = st.text_input("Objet", "Où est ma commande ?")
        corps = st.text_area("Courriel", "Bonjour, ma commande 48213 n'est toujours pas arrivée. Merci de vérifier.")
        st.form_submit_button("Valider le courriel")
    courriel = Courriel(id="LIBRE", expediteur="client@courriel.ca", nom=nom, objet=objet, corps=corps)

if st.button("▶ Traiter le courriel", type="primary", disabled=not pret):
    agent = construire_agent(commun.extracteur(), commun.systemes(), traceur=commun.traceur())
    etat, chemin = etat_initial(courriel), []
    with st.status("L'agent travaille…", expanded=True) as statut:
        # stream_mode="updates" : on reçoit la sortie de chaque nœud dès qu'il a fini
        for mise_a_jour in agent.stream(etat, config_execution(), stream_mode="updates"):
            for noeud, sortie in mise_a_jour.items():
                chemin.append(noeud)
                etat.update({k: v for k, v in (sortie or {}).items() if k != "actions"})
                etat["actions"] = etat.get("actions", []) + (sortie or {}).get("actions", [])
                st.write(f"✓ **{noeud}**")
                zone_schema.graphviz_chart(commun.schema_graphe(chemin), width="stretch")
        statut.update(label="Traitement terminé", state="complete", expanded=False)
    commun.afficher_resultat(etat)
    if etat.get("statut") == "en_attente_validation":
        st.warning("Ici le remboursement reste en attente. Voir la page **Humain dans la boucle** pour la validation.")

commun.afficher_systemes()
