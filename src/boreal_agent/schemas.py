"""Les objets qui circulent dans l'agent.

`Extraction` est le contrat imposé au LLM : il ne peut répondre qu'avec ces champs
et ces valeurs (sortie structurée, module 8).
"""

from typing import Literal

from pydantic import BaseModel, Field

Intention = Literal["suivi", "retard_livraison", "facturation", "remboursement", "autre"]
Sentiment = Literal["positif", "neutre", "irrite"]
Urgence = Literal["basse", "normale", "elevee"]
TypeAction = Literal["reponse_auto", "validation_humaine", "escalade"]


def dollars(montant: float, decimales: int = 2) -> str:
    """Montant au format québécois : 5 000,00 $."""
    texte = f"{montant:,.{decimales}f}".replace(",", " ").replace(".", ",")
    return f"{texte} $"


class Courriel(BaseModel):
    id: str
    expediteur: str
    nom: str
    objet: str
    corps: str

    @property
    def texte(self) -> str:
        return f"Objet : {self.objet}\n\n{self.corps}"


class Extraction(BaseModel):
    """Champs extraits par le LLM à partir d'un courriel client."""

    intention: Intention = Field(
        description=(
            "suivi = où en est ma commande ; retard_livraison = la commande devait déjà être arrivée ; "
            "facturation = erreur ou question sur une facture, double débit ; "
            "remboursement = demande explicite d'être remboursé ou de retourner un produit ; autre = tout le reste"
        )
    )
    # Champs obligatoires mais pouvant valoir null : le modèle doit se prononcer, il ne peut pas les omettre
    numero_commande: str | None = Field(
        description="Numéro de commande à 5 chiffres, sans « # ». null s'il est absent."
    )
    montant: float | None = Field(
        description="Montant en dollars écrit dans le courriel (389,99 → 389.99). null s'il est absent."
    )
    sentiment: Sentiment = Field(
        description="irrite seulement en cas de colère, d'exaspération ou de menace ; une demande polie est neutre"
    )
    urgence: Urgence = Field(description="elevee si ultimatum ou menace ; basse pour une simple question ; sinon normale")
    resume: str = Field(description="Une phrase neutre, à la 3e personne, pour une conseillère")


class Commande(BaseModel):
    numero: str
    client: str
    produit: str
    total: float
    statut: Literal["en_preparation", "expediee", "livree"]
    date_prevue: str
    retard_jours: int = 0
    lien_suivi: str | None = None


class Decision(BaseModel):
    action: TypeAction
    motif: str
    credit: float = 0.0
    montant_remboursement: float = 0.0
    priorite: Literal["normale", "haute"] = "normale"
    brouillon: str = ""
