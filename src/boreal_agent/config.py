"""Paramètres du projet, lus dans l'environnement (fichier .env à la racine)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parents[2]
load_dotenv(RACINE / ".env")


@dataclass(frozen=True)
class Parametres:
    # Modèle local servi par Ollama
    modele: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma4"))
    url_ollama: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    # 8 192 jetons suffisent pour un courriel et gardent le modèle sur un GPU de 8 Go
    contexte: int = field(default_factory=lambda: int(os.getenv("OLLAMA_NUM_CTX", "8192")))

    # Règles métier de Boréal (module 8, « Décider et agir »)
    seuil_commande: float = 500.0  # retard sur une commande < 500 $ → réponse auto + crédit
    credit_retard: float = 15.0  # geste commercial accordé automatiquement

    # Garde-fou codé dans l'outil (module 6, « Sécurité ») : aucun prompt ne peut le dépasser
    plafond_credit: float = field(default_factory=lambda: float(os.getenv("PLAFOND_CREDIT", "500")))

    dossier_donnees: Path = RACINE / "donnees"
    dossier_traces: Path = RACINE / "traces"
    dossier_rapports: Path = RACINE / "rapports"


PARAMS = Parametres()
