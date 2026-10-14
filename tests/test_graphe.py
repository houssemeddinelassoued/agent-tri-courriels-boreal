from boreal_agent.graphe import config_execution, construire_agent, nouveau_checkpointer, reprendre, traiter
from boreal_agent.traces import Traceur, lire_traces


def test_courriel_a_traite_automatiquement(extracteur, systemes, courriels):
    etat = traiter(construire_agent(extracteur, systemes), courriels["A"])
    assert etat["statut"] == "traite_automatiquement"
    assert len(systemes.courriels_envoyes) == 1
    assert list(systemes.credits.values())[0]["montant"] == 15.0


def test_courriel_c_escalade(extracteur, systemes, courriels):
    etat = traiter(construire_agent(extracteur, systemes), courriels["C"])
    assert etat["statut"] == "escalade"
    assert systemes.tickets[0]["priorite"] == "haute"


def test_courriel_piege_bloque(extracteur, systemes, courriels):
    etat = traiter(construire_agent(extracteur, systemes), courriels["D"])
    assert etat["statut"] == "escalade"
    assert systemes.credits == {}  # aucun crédit, ni de 5 000 $ ni d'un autre montant


def test_sans_humain_le_remboursement_reste_en_attente(extracteur, systemes, courriels):
    etat = traiter(construire_agent(extracteur, systemes), courriels["B"])
    assert etat["statut"] == "en_attente_validation"
    assert systemes.remboursements == []


def test_humain_dans_la_boucle_approuve(extracteur, systemes, courriels):
    agent = construire_agent(extracteur, systemes, humain_dans_la_boucle=True, checkpointer=nouveau_checkpointer())
    config = config_execution()
    etat = traiter(agent, courriels["B"], config)
    assert "__interrupt__" in etat  # le graphe est en pause
    assert systemes.remboursements == []
    etat = reprendre(agent, config, "approuver", par="Chantal (conseillère)")
    assert etat["statut"] == "rembourse_apres_validation"
    assert systemes.remboursements[0]["approuve_par"] == "Chantal (conseillère)"


def test_humain_dans_la_boucle_refuse(extracteur, systemes, courriels):
    agent = construire_agent(extracteur, systemes, humain_dans_la_boucle=True, checkpointer=nouveau_checkpointer())
    config = config_execution()
    traiter(agent, courriels["B"], config)
    etat = reprendre(agent, config, "refuser", par="Chantal", commentaire="Vérifier le relevé bancaire")
    assert etat["statut"] == "escalade"
    assert systemes.remboursements == []
    assert "Vérifier le relevé" in systemes.tickets[0]["motif"]


def test_traces_une_ligne_par_etape(extracteur, systemes, courriels, tmp_path):
    traceur = Traceur(tmp_path / "t.jsonl", extracteur=extracteur)
    traiter(construire_agent(extracteur, systemes, traceur=traceur), courriels["A"])
    traces = lire_traces(tmp_path / "t.jsonl")
    assert [t["noeud"] for t in traces] == ["lire", "extraire", "consulter", "decider", "repondre"]
    assert all(t["statut"] == "ok" for t in traces)
    assert "jetons" in traces[1]


def test_sans_filtre_les_regles_protegent_encore(extracteur, systemes, courriels):
    # Le LLM a même extrait 5 000 $ : c'est la règle qui fixe le crédit, pas le courriel
    etat = traiter(construire_agent(extracteur, systemes, filtre_injection=False), courriels["D"])
    assert etat["statut"] == "traite_automatiquement"
    assert [c["montant"] for c in systemes.credits.values()] == [15.0]
