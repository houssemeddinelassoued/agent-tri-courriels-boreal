"""Faux systèmes de Boréal : ERP (commandes), messagerie, crédits, remboursements, billetterie.

Tout reste en mémoire : aucune donnée réelle n'est touchée. Chaque outil applique
les bonnes pratiques du module 7 : permissions minimales, idempotence,
validation humaine pour l'irréversible et messages d'erreur explicites.
"""

import json
from pathlib import Path

from boreal_agent.config import PARAMS
from boreal_agent.garde_fous import GardeFouDeclenche
from boreal_agent.schemas import Commande, dollars


class SystemesBoreal:
    def __init__(self, commandes: dict[str, Commande], plafond_credit: float = PARAMS.plafond_credit):
        self.commandes = commandes
        self.plafond_credit = plafond_credit
        self.courriels_envoyes: list[dict] = []
        self.credits: dict[str, dict] = {}  # clé d'idempotence → crédit
        self.remboursements: list[dict] = []
        self.tickets: list[dict] = []

    @classmethod
    def depuis_fichier(cls, chemin: Path | None = None) -> "SystemesBoreal":
        chemin = chemin or PARAMS.dossier_donnees / "commandes.json"
        brut = json.loads(chemin.read_text(encoding="utf-8"))
        return cls({c["numero"]: Commande(**c) for c in brut})

    # ── ERP : lecture seule ────────────────────────────────────────────────
    def consulter_commande(self, numero: str | None) -> Commande | None:
        if not numero:
            return None
        return self.commandes.get(numero.lstrip("#").strip())

    # ── Messagerie ─────────────────────────────────────────────────────────
    def envoyer_courriel(self, destinataire: str, objet: str, corps: str) -> str:
        self.courriels_envoyes.append({"a": destinataire, "objet": objet, "corps": corps})
        return f"Courriel envoyé à {destinataire}"

    # ── Crédits : plafond codé dans l'outil + idempotence ─────────────────
    def accorder_credit(self, numero: str, montant: float, motif: str, cle: str) -> str:
        if montant <= 0:
            raise ValueError("Le montant du crédit doit être positif.")
        if montant > self.plafond_credit:
            raise GardeFouDeclenche(
                f"Crédit de {dollars(montant)} refusé : le plafond de {dollars(self.plafond_credit, 0)} "
                "est codé dans l'outil. Escalade vers une conseillère."
            )
        if cle in self.credits:
            return f"Crédit déjà accordé pour cette demande (clé {cle}) : aucun doublon."
        self.credits[cle] = {"commande": numero, "montant": montant, "motif": motif}
        return f"Crédit de {dollars(montant)} accordé sur la commande {numero}"

    # ── Remboursements : irréversible → validation humaine obligatoire ────
    def rembourser(self, numero: str, montant: float, approuve_par: str | None) -> str:
        if not approuve_par:
            raise GardeFouDeclenche("Remboursement refusé : aucune validation humaine enregistrée.")
        commande = self.commandes.get(numero)
        if commande is None:
            raise ValueError(f"Commande {numero} inconnue : 5 chiffres attendus.")
        if montant > commande.total:
            raise GardeFouDeclenche(
                f"Remboursement de {dollars(montant)} refusé : supérieur au total de la commande ({dollars(commande.total)})."
            )
        self.remboursements.append({"commande": numero, "montant": montant, "approuve_par": approuve_par})
        return f"Remboursement de {dollars(montant)} effectué sur la commande {numero} (approuvé par {approuve_par})"

    # ── Billetterie ────────────────────────────────────────────────────────
    def creer_ticket(self, courriel_id: str, resume: str, motif: str, priorite: str) -> str:
        numero = f"ESC-{1001 + len(self.tickets)}"
        self.tickets.append(
            {"ticket": numero, "courriel": courriel_id, "resume": resume, "motif": motif, "priorite": priorite}
        )
        return f"Billet {numero} créé (priorité {priorite}) pour une conseillère"
