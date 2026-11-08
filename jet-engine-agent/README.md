# Agent IA « Conception de moteurs à réaction »

Agent conversationnel spécialisé **exclusivement** dans la conception des moteurs
à réaction (turboréacteurs simple flux / *turbojet engines*, turbosoufflantes,
turbopropulseurs, statoréacteurs et leurs composants). Toute demande hors de ce
domaine est refusée. Questions acceptées en français et en anglais.

## Deux façons de l'utiliser

| | Programme autonome (`python -m jetagent`) | Dans Claude Code (skill `jet-engine-agent`) |
|---|---|---|
| Modèle de langage | API Anthropic, **clé API requise** | Fourni par Claude Code, **aucune clé** |
| Outils de calcul | appelés par le modèle (tool use) | `python -m jetagent.cli_tools …` lancé par Claude |
| Où ça tourne | votre machine / serveur | la session Claude Code (web, mobile, terminal) |

Dans Claude Code, ouvrez ce dépôt et tapez `/jet-engine-agent` suivi de votre
question, ou demandez explicitement « l'expert moteur » (sous-agent
`jet-engine-expert`). Les deux modes partagent le même prompt système, la même
base documentaire et les mêmes calculs.

## Architecture

```
jet-engine-agent/
├── jetagent/
│   ├── agent.py       # boucle Claude + outils, garde-fous de périmètre, CLI
│   ├── tools.py       # outils exposés au modèle (@beta_tool)
│   ├── cli_tools.py   # mêmes outils en ligne de commande, sans modèle ni clé
│   ├── cycle.py       # analyse de cycle turboréacteur (déterministe, testée)
│   └── knowledge.py   # recherche BM25 bilingue dans knowledge/*.md
├── knowledge/         # base documentaire (Markdown, extensible)
│   ├── 01_principes_fondamentaux.md   04_certification_normes.md
│   ├── 02_composants.md               05_turbojet_engine.md
│   ├── 03_materiaux.md                06_glossaire_fr_en.md
└── tests/             # tests unitaires (sans appel API)
../.claude/skills/jet-engine-agent/SKILL.md   # skill Claude Code (mode sans clé)
../.claude/agents/jet-engine-expert.md        # sous-agent Claude Code
```

Trois niveaux de spécialisation :

1. **Pré-filtre local** (`is_in_scope`) : rejette gratuitement les demandes
   manifestement hors sujet avant d'appeler le modèle.
2. **Prompt système strict** : périmètre, méthode d'ingénieur, posture
   (assistant, pas autorité de certification), refus des hors-sujets même
   sous insistance.
3. **Outils déterministes** : le modèle doit calculer plutôt qu'estimer.
   - `analyser_cycle_turboreacteur` : cycle réel simple flux (stations 0→9,
     richesse, poussée spécifique, TSFC, rendements), sec ou avec
     post-combustion (afterburner), tuyère convergente ou
     convergente-divergente, atmosphère ISA.
   - `atmosphere_standard` : conditions ISA jusqu'à 32 km.
   - `rechercher_documentation` : recherche dans `knowledge/` (citations de source).
   - `convertir_unites` : poussée, TSFC, pression, vitesse, température…

Modèle : `claude-opus-5-5` par défaut (réflexion adaptative, effort `high`),
avec repli serveur `fallbacks="default"` activé en cas de refus du filtre de
sécurité. Prompt système mis en cache (`cache_control`).

## Installation

```bash
cd jet-engine-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # ou `ant auth login`
```

## Utilisation

```bash
# Mode interactif
python -m jetagent

# Question unique
python -m jetagent "Compare OPR 20 et OPR 30 à T4 = 1600 K en croisière M0,85 / 11 km"

# Voir les appels d'outils, changer l'effort ou le modèle
python -m jetagent -v --effort xhigh "Quel T4 viser pour une turbosoufflante BPR 10 ?"
JETAGENT_MODEL=claude-sonnet-5-5 python -m jetagent "..."
```

Commandes interactives : `reset` (effacer le contexte), `quit`.

## Outils seuls, sans clé API

```bash
python -m jetagent.cli_tools cycle --mach 2 --altitude 15000 --opr 8 --t4 1600 \
    --rechauffe 2000 --tuyere convergent_divergent --debit 70
python -m jetagent.cli_tools doc "turbojet afterburner TSFC"
python -m jetagent.cli_tools isa 11000
python -m jetagent.cli_tools convert 10000 lbf kN
```

## Tests (sans clé API)

```bash
python -m pytest tests -q
```

## Étendre la base de connaissances

Déposez des fichiers `.md` dans `knowledge/`. Chaque titre `#`/`##` devient une
section indexée. Pour une base volumineuse (manuels, normes complètes),
remplacer `knowledge.py` par un index vectoriel.

## Limites du modèle de cycle

Simple flux, gaz parfait à propriétés constantes par section (γ = 1,4 air /
1,33 gaz chauds, y compris en réchauffe), kérosène Jet A-1 (43 MJ/kg). Tuyère
convergente amorcée (poussée de pression ajoutée) ou convergente-divergente
supposée adaptée (P9 = P0). Pas de prélèvement d'air de refroidissement ni de
puissance accessoire. Les résultats sont des
ordres de grandeur de pré-dimensionnement, à confirmer avec un code de cycle
complet (NPSS, GasTurb, pyCycle) puis par essais.
