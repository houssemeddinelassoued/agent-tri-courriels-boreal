"""Exemple 3 · Évaluation et KPI (module 10).

On fait passer à l'agent les 12 courriels du jeu de test « doré » (réponse attendue connue),
puis on calcule les KPI : exactitude, taux d'automatisation, d'escalade, erreurs graves, latence.
Le rapport complet est enregistré dans rapports/.

Lancer :  uv run python exemples/03_evaluation_kpi.py
"""

from boreal_agent.console import FIN, GRAS, ROUGE, VERT, exiger_ollama, note, titre
from boreal_agent.donnees import charger_jeu_de_test
from boreal_agent.evaluation import evaluer, sauvegarder_rapport
from boreal_agent.extraction import ExtracteurOllama

exiger_ollama()
extracteur = ExtracteurOllama()
jeu = charger_jeu_de_test()

titre(f"Évaluation sur {len(jeu)} courriels · modèle {extracteur.modele}")
resultats, kpis = evaluer(extracteur, jeu, progression=lambda i, n, objet: note(f"[{i:2}/{n}] {objet}"))


def ok(valeur: bool) -> str:
    return f"{VERT}✓{FIN}" if valeur else f"{ROUGE}✗{FIN}"


titre("Résultats par courriel")
print(f"  {GRAS}{'Cas':<4} {'Intention':<18} {'N°':<7} {'Décision obtenue':<20} {'Attendue':<20} Durée{FIN}")
for r in resultats:
    grave = f" {ROUGE}ERREUR GRAVE{FIN}" if r.erreur_grave else ""
    print(
        f"  {r.id:<4} {ok(r.ok_intention)} {r.intention_obtenue:<16} {ok(r.ok_numero)} {str(r.numero_obtenu):<5} "
        f"{ok(r.ok_action)} {r.action_obtenue:<18} {r.action_attendue:<20} {r.duree_s:.1f} s{grave}"
    )

titre("KPI")
print(f"  Qualité      · exactitude de l'intention : {kpis['exactitude_intention']} %")
print(f"               · exactitude du n° de commande : {kpis['exactitude_numero']} %")
print(f"               · exactitude de la décision : {kpis['exactitude_decision']} %")
print(f"  Efficacité   · taux d'automatisation : {kpis['taux_automatisation']} %")
print(f"               · latence moyenne : {kpis['latence_moyenne_s']} s par courriel")
print(f"  Charge humaine · validations : {kpis['taux_validation_humaine']} % · escalades : {kpis['taux_escalade']} %")
couleur = VERT if kpis["erreurs_graves"] == 0 else ROUGE
print(f"  Risque       · {couleur}erreurs graves (automatisé à tort) : {kpis['erreurs_graves']}{FIN}")

chemin = sauvegarder_rapport(resultats, kpis, extracteur.modele)
note(f"\nRapport enregistré : {chemin}")
note("Chaque erreur vue en production devient un nouveau cas de test (module 10, amélioration continue).")
