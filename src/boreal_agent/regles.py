"""La règle métier de Boréal, écrite par Boréal et exécutée par du code (module 8).

Retard ET commande < 500 $ → réponse automatique + crédit de 15 $.
Sinon, ou client mécontent → escalade vers une conseillère.
Facturation et remboursement → l'agent prépare, un humain valide.

Aucune de ces décisions n'est confiée au LLM : elles sont testables et auditables.
"""

from boreal_agent.config import PARAMS, Parametres
from boreal_agent.schemas import Commande, Courriel, Decision, Extraction, dollars


def _escalade(motif: str, extraction: Extraction | None) -> Decision:
    priorite = "haute" if extraction is not None and extraction.urgence == "elevee" else "normale"
    return Decision(action="escalade", motif=motif, priorite=priorite)


def decider(
    extraction: Extraction,
    commande: Commande | None,
    alertes: list[str],
    courriel: Courriel,
    p: Parametres = PARAMS,
) -> Decision:
    if alertes:
        return _escalade("Garde-fou : instruction suspecte détectée dans le courriel.", extraction)

    if extraction.sentiment == "irrite":
        return _escalade("Client mécontent : une conseillère reprend la relation.", extraction)

    if extraction.intention in ("facturation", "remboursement"):
        if commande is None:
            return _escalade("Commande introuvable : impossible de vérifier la facturation.", extraction)
        montant = extraction.montant or commande.total
        if montant > commande.total:
            return _escalade("Montant réclamé supérieur au total de la commande.", extraction)
        return Decision(
            action="validation_humaine",
            motif="L'argent du client est en jeu : l'agent prépare, un humain valide.",
            montant_remboursement=montant,
            brouillon=_brouillon_remboursement(courriel, commande, montant),
        )

    if extraction.intention in ("suivi", "retard_livraison"):
        if commande is None:
            return _escalade("Numéro de commande absent ou inconnu.", extraction)
        if commande.retard_jours > 0:
            if commande.total < p.seuil_commande:
                return Decision(
                    action="reponse_auto",
                    motif=f"Retard sur une commande de moins de {dollars(p.seuil_commande, 0)} : réponse + crédit.",
                    credit=p.credit_retard,
                    brouillon=_brouillon_suivi(courriel, commande, p.credit_retard),
                )
            return _escalade(f"Retard sur une commande de {dollars(p.seuil_commande, 0)} ou plus.", extraction)
        return Decision(
            action="reponse_auto",
            motif="Simple suivi d'une commande dans les délais.",
            brouillon=_brouillon_suivi(courriel, commande, 0.0),
        )

    return _escalade("Demande hors du périmètre de l'agent.", extraction)


# ── Brouillons : gabarits approuvés par le service client (pas de texte libre du LLM) ──


def _prenom(courriel: Courriel) -> str:
    return courriel.nom.split()[0] if courriel.nom else ""


def _brouillon_suivi(courriel: Courriel, commande: Commande, credit: float) -> str:
    etat = {
        "en_preparation": "est en préparation dans notre centre de distribution",
        "expediee": "a été expédiée",
        "livree": "a été livrée",
    }[commande.statut]
    lignes = [f"Bonjour {_prenom(courriel)},", "", f"Votre commande {commande.numero} ({commande.produit}) {etat}."]
    if commande.retard_jours > 0:
        lignes.append(
            f"Elle accuse un retard de {commande.retard_jours} jour(s) ; nouvelle date prévue : {commande.date_prevue}."
        )
    else:
        lignes.append(f"Date de livraison prévue : {commande.date_prevue}.")
    if commande.lien_suivi:
        lignes.append(f"Suivi en temps réel : {commande.lien_suivi}")
    if credit:
        lignes.append(f"Pour nous excuser du retard, un crédit de {dollars(credit)} a été ajouté à votre compte.")
    lignes += ["", "L'équipe du service client de Boréal Distribution"]
    return "\n".join(lignes)


def _brouillon_remboursement(courriel: Courriel, commande: Commande, montant: float) -> str:
    return "\n".join(
        [
            f"Bonjour {_prenom(courriel)},",
            "",
            f"Nous avons vérifié votre commande {commande.numero} ({commande.produit}).",
            f"Un remboursement de {dollars(montant)} a été émis ; il apparaîtra sur votre relevé d'ici 3 à 5 jours ouvrables.",
            "",
            "L'équipe du service client de Boréal Distribution",
        ]
    )
