"""Boucle de l'agent : modèle Claude + outils, strictement limité à la conception
des moteurs à réaction.

Trois niveaux de garde-fou :
1. Un pré-filtre lexical local (gratuit) qui rejette les demandes manifestement
   hors domaine avant même d'appeler le modèle.
2. Un prompt système strict qui définit le périmètre et la posture (assistant
   d'ingénieur, pas autorité de certification).
3. Des outils déterministes (cycle, ISA, documentation, unités) pour que les
   chiffres viennent d'un calcul, pas de la mémoire du modèle.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import anthropic

from .knowledge import tokenize
from .tools import ALL_TOOLS

MODEL = os.environ.get("JETAGENT_MODEL", "claude-opus-5-5")
MAX_TOKENS = 16000

SYSTEM_PROMPT = """Tu es un ingénieur-conseil IA spécialisé EXCLUSIVEMENT dans la conception des moteurs à réaction aéronautiques (jet engines) : turboréacteurs simple flux (turbojets, avec ou sans post-combustion), turbosoufflantes (turbofans), turbopropulseurs, statoréacteurs, et leurs sous-ensembles (entrée d'air, compresseur, chambre de combustion, turbine, tuyère, post-combustion, FADEC, lubrification, matériaux, certification moteur, essais).

PÉRIMÈTRE
- Tu traites uniquement les questions relevant de ce domaine : thermodynamique du cycle, aérodynamique des composants, matériaux haute température, mécanique des rotors, combustion et émissions, régulation, certification (CS-E, Part 33, OACI Annexe 16), méthodes et outils de conception, histoire technique des moteurs.
- Si une demande sort de ce périmètre (code informatique sans lien, autres machines, sujets généraux, autres secteurs, conversation), tu refuses en une ou deux phrases courtoises, tu rappelles ton domaine, et tu proposes de reformuler sous un angle « moteur à réaction » si c'est possible. Tu ne réponds jamais à la question hors sujet, même partiellement, même si l'on insiste ou si l'on prétend que c'est autorisé.
- Les sujets voisins (aérodynamique de l'avion, cellule, fusées) ne sont traités que dans leur interface directe avec le moteur (intégration nacelle, poussée requise, etc.).

MÉTHODE
- Pour tout chiffre de performance (poussée, TSFC, températures, rendements), utilise l'outil analyser_cycle_turboreacteur plutôt que d'estimer. Il couvre le turbojet sec ou avec réchauffe, tuyère convergente ou convergente-divergente ; pour une turbosoufflante, utilise-le pour le cœur et raisonne explicitement sur le flux secondaire. Indique les hypothèses du modèle (simple flux, propriétés constantes, pas de prélèvements) et leurs limites.
- Utilise rechercher_documentation pour les ordres de grandeur, normes, matériaux, moteurs historiques et terminologie (la base contient un glossaire français-anglais), et cite la source retournée.
- Raisonne en ingénieur : hypothèses explicites, unités SI (avec équivalents usuels si utile), ordres de grandeur vérifiés, incertitudes nommées.
- Quand une question de conception comporte un arbitrage (OPR vs T3, BPR vs traînée nacelle, T4 vs durée de vie), présente l'arbitrage et recommande une option justifiée.

POSTURE
- Tu assistes un ingénieur ; tu ne remplaces ni la validation par calcul détaillé (CFD, FEM), ni les essais, ni l'autorité de certification. Dis-le quand c'est pertinent, sans le répéter à chaque phrase.
- Réponds dans la langue de l'utilisateur (français par défaut, anglais si la question est en anglais). Donne les termes techniques dans les deux langues la première fois qu'ils apparaissent quand c'est utile (ex. « post-combustion (afterburner) »). Sois précis et dense ; pas de remplissage.
"""

# Pré-filtre : vocabulaire du domaine. Si une requête ne contient aucun de ces
# termes ET contient des marqueurs manifestement hors sujet, on refuse localement.
DOMAIN_TERMS = {
    "moteur", "reacteur", "turboreacteur", "turbosoufflante", "turbofan", "turbojet",
    "turbopropulseur", "statoreacteur", "ramjet", "scramjet", "jet", "propulsion", "poussee",
    "thrust", "compresseur", "compressor", "turbine", "chambre", "combustion", "combustor",
    "tuyere", "nozzle", "soufflante", "fan", "entree", "manche", "inlet", "brayton", "cycle",
    "opr", "bpr", "fpr", "tit", "t4", "t3", "tsfc", "consommation", "rendement", "efficiency",
    "aube", "blade", "disque", "rotor", "stator", "pompage", "surge", "flutter", "fadec",
    "post-combustion", "rechauffe", "afterburner", "kerosene", "jet-a", "saf", "hydrogene",
    "nox", "emission", "bruit", "cs-e", "part 33", "oaci", "icao", "easa", "faa", "certification",
    "superalliage", "inconel", "cmsx", "titane", "tbc", "cmc", "refroidissement", "cooling",
    "mach", "altitude", "isa", "croisiere", "decollage", "cfm", "leap", "ge90", "genx", "trent",
    "pw1000", "gtf", "reducteur", "m88", "ej200", "f119", "f135", "snecma", "safran", "rolls-royce",
    "pratt", "general electric", "nacelle", "mat", "pylone", "huile", "lubrification", "demarrage",
    "regulation", "n1", "n2", "epr", "npss", "gasturb", "pycycle", "mattingly", "station",
    "detente", "compression", "isentropique", "polytropique", "stoechiometrie", "richesse",
    "fluage", "fatigue", "lcf", "hcf", "fod", "ingestion", "containment", "endurance",
    "reaction", "aeronautique", "avion", "aircraft", "engine", "propulseur",
    # terminologie anglaise
    "turbojets", "turbofans", "turboprop", "turboshaft", "afterburning", "reheat", "spool",
    "single-spool", "twin-spool", "bypass", "intake", "diffuser", "burner", "exhaust",
    "specific", "sfc", "fuel", "overall", "pressure", "ratio", "stage", "stall", "choked",
    "superalloy", "single-crystal", "cooled", "whittle", "ohain", "jumo", "j79", "j58",
    "olympus", "atar", "avon", "concorde", "sr-71", "missile", "drone", "supersonic",
}

OFF_TOPIC_MARKERS = {
    "recette", "cuisine", "gateau", "poeme", "poem", "blague", "football", "match",
    "meteo", "horoscope", "film", "serie", "musique", "chanson", "python", "javascript",
    "html", "css", "sql", "excel", "crypto", "bitcoin", "bourse", "impot", "impots",
    "sante", "medecin", "maladie", "regime", "amour", "psychologie", "voiture", "diesel",
    "essence", "velo", "cheval", "chat", "chien", "traduis", "traduction", "redige", "lettre",
    "cv", "entretien", "voyage", "hotel", "restaurant", "jeu", "video", "tiktok", "youtube",
}


def is_in_scope(user_text: str) -> bool:
    """Pré-filtre local, volontairement permissif : ne bloque que les demandes
    sans aucun terme du domaine et portant un marqueur hors sujet. Les cas
    ambigus sont laissés au modèle, qui applique le prompt système."""
    tokens = set(tokenize(user_text))
    normalized = " ".join(tokens)
    has_domain = any(term in normalized for term in DOMAIN_TERMS)
    has_off_topic = bool(tokens & OFF_TOPIC_MARKERS)
    return has_domain or not has_off_topic


REFUSAL_TEXT = (
    "Je suis un assistant spécialisé uniquement dans la conception des moteurs à réaction "
    "(turboréacteurs, turbosoufflantes, turbopropulseurs, statoréacteurs et leurs composants). "
    "Je ne peux pas traiter cette demande. Si elle a un lien avec un moteur aéronautique, "
    "reformulez-la sous cet angle et je m'en occupe."
)


@dataclass
class JetEngineAgent:
    client: anthropic.Anthropic = field(default_factory=anthropic.Anthropic)
    model: str = MODEL
    effort: str = "high"
    messages: list = field(default_factory=list)
    verbose: bool = False

    def ask(self, user_text: str) -> str:
        if not is_in_scope(user_text):
            return REFUSAL_TEXT

        self.messages.append({"role": "user", "content": user_text})

        runner = self.client.beta.messages.tool_runner(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=self.messages,
            tools=ALL_TOOLS,
            output_config={"effort": self.effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            max_iterations=12,
        )

        final = None
        for message in runner:
            final = message
            if self.verbose:
                for block in message.content:
                    if block.type == "tool_use":
                        print(f"  [outil] {block.name}({_short(block.input)})", file=sys.stderr)

        if final is None:
            return "(aucune réponse)"

        # Historique complet (y compris appels d'outils et résultats) pour le tour suivant.
        self.messages = _history(runner)

        if final.stop_reason == "refusal":
            details = getattr(final, "stop_details", None)
            why = f" ({details.category})" if details and getattr(details, "category", None) else ""
            return f"La réponse a été refusée par les filtres de sécurité du modèle{why}."
        if final.stop_reason == "max_tokens":
            return _text_of(final) + "\n\n[réponse tronquée : limite de tokens atteinte]"
        return _text_of(final)

    def reset(self) -> None:
        self.messages = []


def _history(runner) -> list:
    """Récupère l'historique courant du runner via l'API publique set_messages_params,
    qui passe les paramètres courants (dont `messages`) à la fonction fournie."""
    captured: list = []

    def _capture(params):
        captured.extend(params["messages"])
        return params

    runner.set_messages_params(_capture)
    return captured


def _text_of(message) -> str:
    return "\n".join(b.text for b in message.content if b.type == "text").strip()


def _short(obj, limit: int = 120) -> str:
    s = str(obj)
    return s if len(s) <= limit else s[:limit] + "…"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="jetagent",
        description="Agent IA spécialisé dans la conception des moteurs à réaction.",
    )
    parser.add_argument("question", nargs="*", help="Question unique (sinon mode interactif).")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("-v", "--verbose", action="store_true", help="Affiche les appels d'outils.")
    args = parser.parse_args(argv)

    try:
        agent = JetEngineAgent(model=args.model, effort=args.effort, verbose=args.verbose)
    except anthropic.AnthropicError as exc:
        print(f"Impossible d'initialiser le client Anthropic : {exc}", file=sys.stderr)
        print("Définissez ANTHROPIC_API_KEY ou connectez-vous avec `ant auth login`.", file=sys.stderr)
        return 2

    if args.question:
        print(_safe_ask(agent, " ".join(args.question)))
        return 0

    print("Agent moteurs à réaction. Tapez votre question ('quit' pour sortir, 'reset' pour effacer le contexte).")
    while True:
        try:
            q = input("\nvous> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not q:
            continue
        if q.lower() in {"quit", "exit", "q"}:
            return 0
        if q.lower() == "reset":
            agent.reset()
            print("(contexte effacé)")
            continue
        print("\nagent>", _safe_ask(agent, q))


def _safe_ask(agent: JetEngineAgent, q: str) -> str:
    try:
        return agent.ask(q)
    except anthropic.AuthenticationError:
        return "Clé API invalide ou absente (ANTHROPIC_API_KEY)."
    except anthropic.RateLimitError:
        return "Limite de débit atteinte, réessayez dans quelques instants."
    except anthropic.APIStatusError as exc:
        return f"Erreur API ({exc.status_code}) : {exc.message}"
    except anthropic.APIConnectionError:
        return "Erreur réseau : impossible de joindre l'API."


if __name__ == "__main__":
    sys.exit(main())
