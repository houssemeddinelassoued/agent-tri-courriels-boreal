"""Exemple 3 · Évaluation sur un jeu de test « doré » et KPI (module 10)."""

import json

import pandas as pd
import streamlit as st

import commun
from boreal_agent.config import PARAMS
from boreal_agent.donnees import charger_jeu_de_test
from boreal_agent.evaluation import evaluer, sauvegarder_rapport

pret = commun.configurer_page("Évaluation et KPI", "📊")
st.title("📊 Exemple 3 · Évaluation et KPI")
st.markdown(
    "Avant chaque mise en production, l'agent repasse un **jeu de test « doré »** : 12 courriels dont on "
    "connaît la bonne réponse. Un seul chiffre raconte une demi-vérité : on lit les familles de KPI ensemble."
)

jeu = charger_jeu_de_test()
with st.expander(f"Voir le jeu de test ({len(jeu)} courriels)"):
    st.dataframe(
        pd.DataFrame(
            [
                {"Cas": c.courriel.id, "Objet": c.courriel.objet, "Intention attendue": " / ".join(c.attendu.intentions),
                 "N° attendu": c.attendu.numero_commande, "Décision attendue": c.attendu.action}
                for c in jeu
            ]
        ),
        hide_index=True,
    )

if st.button(f"▶ Lancer l'évaluation (≈ {len(jeu) * 2} s)", type="primary", disabled=not pret):
    barre = st.progress(0.0, text="Démarrage…")
    resultats, kpis = evaluer(
        commun.extracteur(), jeu, progression=lambda i, n, objet: barre.progress((i - 1) / n, text=f"{i}/{n} · {objet}")
    )
    barre.progress(1.0, text="Terminé")
    chemin = sauvegarder_rapport(resultats, kpis, commun.extracteur().modele)
    st.session_state.evaluation = (resultats, kpis, chemin.name)

if "evaluation" in st.session_state:
    resultats, kpis, nom = st.session_state.evaluation
    st.subheader("KPI")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Qualité · décision exacte", f"{kpis['exactitude_decision']} %", border=True,
              help=f"Intention : {kpis['exactitude_intention']} % · n° de commande : {kpis['exactitude_numero']} %")
    c2.metric("Efficacité · automatisation", f"{kpis['taux_automatisation']} %", border=True,
              help=f"Latence moyenne : {kpis['latence_moyenne_s']} s par courriel")
    c3.metric("Charge humaine", f"{kpis['taux_validation_humaine'] + kpis['taux_escalade']:.0f} %", border=True,
              help=f"Validations : {kpis['taux_validation_humaine']} % · escalades : {kpis['taux_escalade']} %")
    c4.metric("Risque · erreurs graves", kpis["erreurs_graves"], border=True,
              help="Courriels traités automatiquement alors qu'un humain devait intervenir")

    st.subheader("Résultats par courriel")
    tableau = pd.DataFrame([r.model_dump() for r in resultats])
    for col in ("ok_intention", "ok_numero", "ok_action"):
        tableau[col] = tableau[col].map({True: "✅", False: "❌"})
    st.dataframe(
        tableau[["id", "objet", "ok_intention", "intention_obtenue", "ok_numero", "numero_obtenu", "ok_action",
                 "action_obtenue", "action_attendue", "duree_s"]],
        hide_index=True,
        column_config={"ok_intention": "Int.", "ok_numero": "N°", "ok_action": "Déc.", "duree_s": "Durée (s)"},
    )
    st.caption(f"Rapport enregistré dans rapports/{nom}")

rapports = sorted(PARAMS.dossier_rapports.glob("evaluation-*.json"), reverse=True)
if rapports:
    st.subheader("Historique des évaluations")
    historique = []
    for chemin in rapports[:10]:
        r = json.loads(chemin.read_text(encoding="utf-8"))
        historique.append({"Date": r["date"], "Modèle": r["modele"], **r["kpis"]})
    st.dataframe(pd.DataFrame(historique), hide_index=True)
    st.caption("Comparez les modèles (OLLAMA_MODEL dans .env) ou l'effet d'une modification du prompt.")
