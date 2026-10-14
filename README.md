# Agent de tri des courriels · Boréal Distribution

Projet de démonstration de la formation « Feuille de route pour l'IA agentique »**.
Il met en code le fil rouge du cours : l'agent qui trie les **5 000 courriels mensuels** du service client
de Boréal Distribution (entreprise fictive).

> **Le LLM comprend, des règles décident, des outils agissent.** (module 8)

| | |
| --- | --- |
| Framework | [LangGraph](https://langchain-ai.github.io/langgraph/) (graphe d'états, pause « humain dans la boucle », checkpointer) |
| Modèle | **gemma4** en local via [Ollama](https://ollama.com) : aucune donnée ne quitte le poste |
| Interface | [Streamlit](https://streamlit.io) (5 pages) + scripts en ligne de commande |
| Données | 100 % fictives : 7 commandes, 4 courriels de démonstration, 12 courriels de test |

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/) et Ollama avec le modèle `gemma4` (`ollama pull gemma4`).

```bash
uv sync                                   # installe Python 3.13 et les dépendances dans .venv
uv run streamlit run app/Accueil.py       # interface web → http://localhost:8501
```

Le premier traitement prend ~20 s (chargement du modèle en mémoire), les suivants ~2 s par courriel.

## Le workflow

```
                                         ┌─ réponse auto ──────► Répondre (+ crédit 15 $)
 Lire → Extraire → Consulter → Décider ──┼─ argent en jeu ─────► Validation humaine ─► Rembourser
 (filtre)  (LLM →    (ERP,      (règles  │                              └─ refus ─┐
           JSON)     lecture)   codées)  └─ sinon ─────────────► Escalader (billet) ◄┘
```

| Étape | Qui | Ce qui se passe | Module |
| --- | --- | --- | --- |
| Lire | code | filtre d'entrée : repère les tournures d'injection de prompt | 6 |
| Extraire | **LLM** | courriel libre → JSON validé par un schéma (intention, n° de commande, montant, sentiment, urgence, résumé) ; un n° absent du courriel est rejeté (anti-hallucination) | 8, 6 |
| Consulter | outil | lecture seule de la commande dans l'ERP | 7 |
| Décider | **règles** | retard ET commande < 500 $ → réponse + crédit ; argent en jeu → validation humaine ; client irrité, gros montant, n° inconnu ou hors périmètre → escalade | 8 |
| Agir | outils | courriel (gabarit approuvé), crédit plafonné et idempotent, remboursement après validation, billet d'escalade | 7 |

Les trois courriels du simulateur du cours donnent les trois issues :
**A** « Où est ma commande #45812 ? » → réponse automatique + crédit ·
**B** facture payée en double → validation humaine ·
**C** client en colère → escalade, priorité haute.

## Les 4 exemples

Chaque concept existe en deux versions : une **page Streamlit** (pour la salle) et un **script** (pour lire le code).

| # | Concept | Page Streamlit | Script |
| --- | --- | --- | --- |
| 0 | Workflow complet, étape par étape | Accueil | `exemples/00_workflow.py` |
| 1 | **Humain dans la boucle** : le graphe se met en pause (`interrupt`) avant tout remboursement et reprend sur décision humaine (`Command(resume=…)`) | Humain dans la boucle | `exemples/01_humain_dans_la_boucle.py` |
| 2 | **Garde-fous et injection** : un agent naïf obéit au courriel piégé (crédit de 5 000 $), l'agent protégé escalade ; le plafond codé dans l'outil refuse même un appel direct | Garde-fous et injection | `exemples/02_garde_fous_injection.py` |
| 3 | **Évaluation et KPI** : 12 courriels « dorés », exactitude, automatisation, charge humaine, erreurs graves, latence ; rapport JSON dans `rapports/` | Évaluation et KPI | `exemples/03_evaluation_kpi.py` |
| 4 | **Journal des traces** : chaque nœud journalisé (durée, statut, sortie, jetons) dans `traces/traces.jsonl` | Journal des traces | `exemples/04_journal_traces.py` |

```bash
uv run python exemples/00_workflow.py
uv run python exemples/01_humain_dans_la_boucle.py            # demande approuver / refuser
uv run python exemples/02_garde_fous_injection.py
uv run python exemples/03_evaluation_kpi.py
uv run python exemples/04_journal_traces.py
```

### Idées de manipulations en salle

- **Page Garde-fous** : désactivez le filtre d'entrée. L'agent protégé n'accorde quand même que 15 $, car c'est la règle qui fixe le montant, pas le courriel. Réécrivez l'attaque pour contourner le filtre.
- **Page Accueil** : écrivez votre propre courriel (sarcasme, deux numéros de commande, anglais…) et observez l'extraction.
- **Évaluation** : changez de modèle (`OLLAMA_MODEL=llama3.2` dans `.env`), relancez, comparez dans l'historique.
- **Règles** : modifiez le seuil de 500 $ dans `src/boreal_agent/config.py` et relancez les tests.

## Structure

```text
agent-tri-courriels-boreal/
├── src/boreal_agent/
│   ├── graphe.py        # le graphe LangGraph (nœuds, routage, pause humaine)
│   ├── extraction.py    # appel au LLM local, sortie structurée, anti-hallucination
│   ├── regles.py        # la règle métier de Boréal, en code testable
│   ├── systemes.py      # faux ERP, messagerie, crédits, remboursements, billetterie
│   ├── garde_fous.py    # filtre d'injection + exception GardeFouDeclenche
│   ├── traces.py        # journal JSONL de chaque nœud
│   ├── evaluation.py    # jeu de test doré et KPI
│   ├── agent_naif.py    # CONTRE-EXEMPLE : l'agent vulnérable du module 6
│   └── schemas.py · config.py · donnees.py · console.py
├── donnees/             # commandes.json, courriels_demo.json, jeu_de_test.json
├── exemples/            # les 5 scripts en ligne de commande
├── app/                 # l'interface Streamlit (Accueil + 4 pages)
└── tests/               # 18 tests, sans Ollama (faux extracteur)
```

## Tests

```bash
uv run pytest
```

Les tests remplacent le LLM par un faux extracteur déterministe : ils vérifient le graphe, les règles,
les garde-fous, la pause humaine et les traces en moins d'une seconde, sans Ollama.

## Réglages

Copiez `.env.example` en `.env` pour changer le modèle, l'adresse d'Ollama, la taille du contexte ou le
plafond de crédit. Avec `gemma4` (9,6 Go) sur un GPU de 8 Go, gardez `OLLAMA_NUM_CTX=8192` : la fenêtre
par défaut (131 072 jetons) déborde de la mémoire vidéo et ralentit fortement le modèle.

## Version web

L'interface est publiée sur [Streamlit Cloud](https://agent-boreal.streamlit.app/) et sur
[GitHub Pages](https://houssemeddinelassoued.github.io/agent-tri-courriels-boreal/). Le serveur de
Streamlit n'a pas de GPU : il joint l'Ollama **de votre poste** par un tunnel [ngrok](https://ngrok.com)
protégé par mot de passe. La version web ne répond donc que lorsque le poste, Ollama et le tunnel sont
allumés ; les courriels transitent alors par ngrok et Streamlit Cloud.

Mise en place (une seule fois) :

1. Créez un compte ngrok gratuit, installez l'agent (`winget install ngrok.ngrok`), puis
   `ngrok config add-authtoken <jeton>` ; notez votre domaine de développement
   (*Universal Gateway → Domains*, du type `xxxx.ngrok-free.dev`).
2. Copiez `deploiement/ngrok-politique.exemple.yml` en `deploiement/ngrok-politique.yml`
   (non versionné) et choisissez un mot de passe.
3. Dans Streamlit Cloud (*Settings → Secrets*) :

   ```toml
   OLLAMA_BASE_URL = "https://boreal:MOT_DE_PASSE@xxxx.ngrok-free.dev"
   OLLAMA_MODEL = "gemma4"
   OLLAMA_NUM_CTX = "8192"
   ```

À chaque séance, Ollama lancé (gardez la fenêtre ouverte pendant la démo) :

```powershell
.\deploiement\tunnel-ollama.ps1
```

Le script lance `ngrok http 11434 --url=https://<domaine> --host-header="localhost:11434" --traffic-policy-file=deploiement/ngrok-politique.yml`.

`--host-header` est indispensable : Ollama refuse (403) les requêtes adressées à un autre nom que `localhost`.

## Pour aller plus loin (module 9)

Ce prototype n'est pas un système de production. Pour un pilote : connecteurs réels (Microsoft Graph,
ERP) avec comptes de service à moindre privilège, checkpointer persistant (`SqliteSaver`, Postgres),
traces vers LangSmith, Langfuse ou OpenTelemetry, évaluation sur des centaines de vrais courriels,
EFVP au sens de la Loi 25 avant de traiter des renseignements personnels.
