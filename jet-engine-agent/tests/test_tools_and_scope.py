import json

from jetagent.agent import REFUSAL_TEXT, is_in_scope
from jetagent.knowledge import KnowledgeBase
from jetagent.tools import (
    analyser_cycle_turboreacteur,
    atmosphere_standard,
    convertir_unites,
    rechercher_documentation,
)


def test_scope_filter_accepts_domain_questions():
    assert is_in_scope("Quel taux de compression viser pour un turboréacteur à Mach 2 ?")
    assert is_in_scope("Explique le pompage du compresseur HP")
    assert is_in_scope("Quelle est la TSFC typique d'une turbosoufflante BPR 10 ?")
    # Ambigu : on laisse le modèle trancher
    assert is_in_scope("Bonjour, peux-tu m'aider ?")


def test_scope_filter_rejects_obvious_off_topic():
    assert not is_in_scope("Donne-moi une recette de gâteau au chocolat")
    assert not is_in_scope("Écris un poème sur l'amour")
    assert not is_in_scope("Écris un script Python qui trie une liste")
    assert REFUSAL_TEXT.startswith("Je suis un assistant spécialisé")


def test_scope_filter_keeps_domain_even_with_off_topic_words():
    # « python » est hors sujet seul, mais ici il sert un calcul de cycle moteur
    assert is_in_scope("Écris un script Python qui calcule le cycle d'un turboréacteur")


def test_knowledge_base_search():
    kb = KnowledgeBase()
    assert len(kb.list_documents()) >= 4
    hits = kb.search("marge au pompage compresseur", top_k=2)
    assert hits and "Compresseur" in hits[0][1].title
    hits = kb.search("ingestion d'oiseaux certification", top_k=2)
    assert any("certification" in s.source for _, s in hits)


def test_cycle_tool_returns_json():
    out = json.loads(analyser_cycle_turboreacteur.call({"mach": 0.0, "taux_compression": 20.0,
                                                        "temperature_entree_turbine_K": 1500.0}))
    assert "specific_thrust_N_per_kg_s" in out
    assert out["nozzle_choked"] is True


def test_cycle_tool_reports_errors_as_json():
    out = json.loads(analyser_cycle_turboreacteur.call({"taux_compression": 0.5}))
    assert "erreur" in out


def test_atmosphere_tool():
    out = json.loads(atmosphere_standard.call({"altitude_m": 0}))
    assert abs(out["temperature_K"] - 288.15) < 1e-6


def test_search_tool():
    out = json.loads(rechercher_documentation.call({"requete": "superalliage monocristallin TBC"}))
    assert out["resultats"]
    assert any("matériaux" in r["source"].lower() or "materiaux" in r["source"].lower()
               for r in out["resultats"])


def test_unit_conversion():
    assert json.loads(convertir_unites.call({"valeur": 1.0, "de": "lb/lbf/h", "vers": "kg/N/h"}))["valeur"] == 0.101972
    assert abs(json.loads(convertir_unites.call({"valeur": 10000, "de": "lbf", "vers": "kN"}))["valeur"] - 44.482216) < 1e-6
    assert json.loads(convertir_unites.call({"valeur": 0, "de": "C", "vers": "K"}))["valeur"] == 273.15
    assert "erreur" in json.loads(convertir_unites.call({"valeur": 1, "de": "kg", "vers": "N"}))


def test_tool_schemas_are_generated():
    schema = analyser_cycle_turboreacteur.to_dict()
    assert schema["name"] == "analyser_cycle_turboreacteur"
    props = schema["input_schema"]["properties"]
    assert "taux_compression" in props and "debit_air_kg_s" in props
