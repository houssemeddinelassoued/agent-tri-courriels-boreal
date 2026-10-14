"""Paramètres du projet, lus dans l'environnement (fichier .env à la racine)."""

import base64
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parents[2]
load_dotenv(RACINE / ".env")


def separer_identifiants(url: str) -> tuple[str, dict[str, str]]:
    """« https://user:mdp@hote » → (« https://hote », en-tête Authorization Basic).

    Sert à joindre un Ollama exposé par un tunnel protégé par mot de passe (version web).
    """
    morceaux = urlsplit(url)
    if not morceaux.username:
        return url.rstrip("/"), {}
    paire = f"{unquote(morceaux.username)}:{unquote(morceaux.password or '')}"
    hote = morceaux.hostname + (f":{morceaux.port}" if morceaux.port else "")
    propre = urlunsplit(morceaux._replace(netloc=hote)).rstrip("/")
    return propre, {"Authorization": "Basic " + base64.b64encode(paire.encode()).decode()}


_URL_OLLAMA, _ENTETES_OLLAMA = separer_identifiants(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))


@dataclass(frozen=True)
class Parametres:
    # Modèle servi par Ollama (en local, ou via un tunnel pour la version web)
    modele: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma4"))
    url_ollama: str = _URL_OLLAMA  # sans identifiants : ils partent dans l'en-tête ci-dessous
    entetes_ollama: dict[str, str] = field(default_factory=lambda: dict(_ENTETES_OLLAMA))
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
