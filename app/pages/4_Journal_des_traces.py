"""Exemple 4 · Journal des traces (modules 9 et 10 · Monitoring)."""

import pandas as pd
import streamlit as st

import commun
from boreal_agent.traces import lire_traces

commun.configurer_page("Journal des traces", "🔎")
st.title("🔎 Exemple 4 · Journal des traces")
st.markdown(
    "Chaque étape de chaque exécution est journalisée dans `traces/traces.jsonl` : nœud, horodatage, durée, "
    "statut, sortie et jetons consommés. C'est ce qui permet d'expliquer une décision, de mesurer les coûts "
    "et de retrouver la cause d'une erreur."
)

traces = lire_traces()
if not traces:
    st.info("Aucune trace pour l'instant : traitez quelques courriels dans les autres pages.")
    st.stop()

df = pd.DataFrame(traces)
executions = (
    df.groupby("execution_id", sort=False)
    .agg(courriel=("courriel_id", "first"), debut=("horodatage", "first"), duree_ms=("duree_ms", "sum"),
         etapes=("noeud", " → ".join), pauses=("statut", lambda s: int((s == "pause").sum())))
    .reset_index()
    .iloc[::-1]
)
jetons = sum((t.get("jetons") or {}).get("total_tokens", 0) for t in traces)

c1, c2, c3 = st.columns(3)
c1.metric("Exécutions journalisées", len(executions), border=True)
c2.metric("Durée moyenne", f"{executions['duree_ms'].mean() / 1000:.1f} s", border=True)
c3.metric("Jetons consommés", f"{jetons:,}".replace(",", " "), border=True, help="Coût en local : nul. En infonuagique : à surveiller.")

st.subheader("Exécutions")
st.dataframe(
    executions,
    hide_index=True,
    column_config={"execution_id": "Exécution", "courriel": "Courriel", "debut": "Début", "duree_ms": "Durée (ms)",
                   "etapes": "Étapes", "pauses": "Pauses humaines"},
)

execution = st.selectbox(
    "Détail d'une exécution",
    executions["execution_id"],
    format_func=lambda e: f"{e} · courriel {executions.set_index('execution_id').loc[e, 'courriel']} · "
    f"{executions.set_index('execution_id').loc[e, 'debut']}",
)
detail = [t for t in traces if t["execution_id"] == execution]
st.bar_chart(pd.DataFrame(detail), x="noeud", y="duree_ms", horizontal=True, sort=False, y_label="Durée (ms)", x_label="")
for t in detail:
    icone = {"ok": "✅", "pause": "⏸️", "erreur": "❌"}[t["statut"]]
    with st.expander(f"{icone} {t['noeud']} · {t['duree_ms']} ms · {t['horodatage']}"):
        if t.get("jetons"):
            st.caption(f"Jetons : {t['jetons']}")
        st.json(t["sortie"])

with st.sidebar:
    if st.button("🗑️ Vider le journal"):
        commun.traceur().fichier.unlink(missing_ok=True)
        st.rerun()
