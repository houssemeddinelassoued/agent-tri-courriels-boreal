"""Garde-fous (module 6 · Sécurité, OWASP LLM01 et LLM06).

Deux couches complémentaires :
1. un filtre d'entrée qui repère les tournures typiques d'une injection de prompt ;
2. des limites codées dans les outils (plafond, validation humaine), voir `systemes.py`.

Le filtre est une couche parmi d'autres : il rate forcément des variantes.
La vraie protection reste la seconde couche, qu'aucun texte ne peut contourner.
"""

import re


class GardeFouDeclenche(Exception):
    """Levée par un outil quand une action dépasse ce qui est autorisé."""


MOTIFS_INJECTION = [
    r"ignore[rsz]?\s+(toutes\s+)?(tes|vos|les)\s+(instructions|consignes|règles)",
    r"oublie[rsz]?\s+(tes|vos|les)\s+(instructions|consignes|règles)",
    r"(nouvelles?|autres?)\s+instructions?\s*:",
    r"tu\s+es\s+(maintenant|désormais)",
    r"prompt\s+(système|systeme)|system\s+prompt",
    r"accorde[rsz]?\s+(un|une|le)\s+(crédit|credit|remboursement)",
    r"réponds?\s+«?\s*approuvé",
]


def detecter_injection(texte: str) -> list[str]:
    """Renvoie les passages suspects trouvés dans le texte (liste vide si rien)."""
    trouves = []
    for motif in MOTIFS_INJECTION:
        m = re.search(motif, texte, flags=re.IGNORECASE)
        if m:
            trouves.append(m.group(0))
    return trouves
