import pytest

from boreal_agent.garde_fous import GardeFouDeclenche, detecter_injection
from boreal_agent.regles import decider
from conftest import EXTRACTIONS


def test_retard_sur_petite_commande_donne_reponse_et_credit(systemes, courriels):
    decision = decider(EXTRACTIONS["A"], systemes.consulter_commande("45812"), [], courriels["A"])
    assert decision.action == "reponse_auto"
    assert decision.credit == 15.0
    assert "https://suivi" in decision.brouillon


def test_retard_sur_grosse_commande_escalade(systemes, courriels):
    extraction = EXTRACTIONS["A"].model_copy(update={"numero_commande": "46550"})
    decision = decider(extraction, systemes.consulter_commande("46550"), [], courriels["A"])
    assert decision.action == "escalade"


def test_client_irrite_escalade_en_priorite_haute(systemes, courriels):
    decision = decider(EXTRACTIONS["C"], systemes.consulter_commande("48001"), [], courriels["C"])
    assert (decision.action, decision.priorite) == ("escalade", "haute")


def test_remboursement_passe_par_un_humain(systemes, courriels):
    decision = decider(EXTRACTIONS["B"], systemes.consulter_commande("47230"), [], courriels["B"])
    assert decision.action == "validation_humaine"
    assert decision.montant_remboursement == 249.5


def test_commande_introuvable_escalade(courriels):
    assert decider(EXTRACTIONS["A"], None, [], courriels["A"]).action == "escalade"


def test_filtre_repere_l_injection(courriels):
    assert detecter_injection(courriels["D"].texte)
    assert detecter_injection(courriels["A"].texte) == []


def test_plafond_code_dans_l_outil(systemes):
    with pytest.raises(GardeFouDeclenche):
        systemes.accorder_credit("45812", 5000, "injection", cle="x")


def test_credit_idempotent(systemes):
    systemes.accorder_credit("45812", 15, "retard", cle="credit-A")
    message = systemes.accorder_credit("45812", 15, "retard", cle="credit-A")
    assert "aucun doublon" in message
    assert len(systemes.credits) == 1


def test_remboursement_sans_validation_refuse(systemes):
    with pytest.raises(GardeFouDeclenche):
        systemes.rembourser("47230", 249.5, approuve_par=None)


def test_numero_absent_du_courriel_est_rejete(courriels):
    from boreal_agent.extraction import verifier_ancrage

    invente = EXTRACTIONS["A"].model_copy(update={"numero_commande": "12345"})
    assert verifier_ancrage(invente, courriels["A"]).numero_commande is None
    avec_diese = EXTRACTIONS["A"].model_copy(update={"numero_commande": "#45812"})
    assert verifier_ancrage(avec_diese, courriels["A"]).numero_commande == "45812"
