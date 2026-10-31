from copy import deepcopy

import pytest

from nexusmind.domain.documents import normalize


def resource(kind="champion", data=None, patch="16.1.1", locale="fr_FR"):
    # Synthetic minimal Data Dragon payload; no assertion about current game balance.
    return {
        "kind": kind,
        "patch": patch,
        "locale": locale,
        "source_url": "https://ddragon.leagueoflegends.com/test.json",
        "retrieved_at": "2026-10-31T12:00:00+00:00",
        "data": data
        if data is not None
        else {
            "data": {
                "Ahri": {
                    "id": "Ahri",
                    "name": "Ahri",
                    "title": "Titre de test",
                    "tags": ["Mage"],
                    "passive": {"name": "Passif test", "description": "<b>Texte</b> &amp; soin."},
                    "spells": [
                        {"id": "TestQ", "name": "Sort test", "description": "Lance un orbe."}
                    ],
                }
            }
        },
    }


def test_champion_sections_are_searchable_and_traceable():
    docs = normalize(resource())
    assert [doc.section for doc in docs] == ["overview", "passive", "spell:TestQ"]
    assert "Texte & soin." in docs[1].text
    assert "<b>" not in docs[1].text
    assert "Ahri" in docs[2].text and "Lance un orbe." in docs[2].text
    assert all(doc.patch == "16.1.1" and doc.locale == "fr_FR" for doc in docs)
    assert all(doc.source_name == "Riot Data Dragon" for doc in docs)


def test_identity_is_stable_but_separates_patch_and_language():
    first = normalize(resource())[0]
    assert first.id == normalize(resource())[0].id
    assert first.id != normalize(resource(patch="16.2.1"))[0].id
    assert first.id != normalize(resource(locale="en_US"))[0].id
    changed = deepcopy(resource())
    changed["data"]["data"]["Ahri"]["title"] = "Changed"
    assert normalize(changed)[0].content_hash != first.content_hash


@pytest.mark.parametrize(
    "kind,data,expected",
    [
        ("item", {"data": {"1001": {"name": "Objet test", "description": "Vitesse"}}}, "1001"),
        (
            "summoner_spell",
            {"data": {"Flash": {"id": "Flash", "name": "Sort", "description": "Texte"}}},
            "Flash",
        ),
        (
            "rune",
            [
                {
                    "id": 8000,
                    "slots": [
                        {"runes": [{"id": 8005, "name": "Rune test", "longDesc": "Description"}]}
                    ],
                }
            ],
            "8005",
        ),
    ],
)
def test_other_official_entities(kind, data, expected):
    docs = normalize(resource(kind=kind, data=data))
    assert len(docs) == 1
    assert docs[0].entity_id == expected
    assert docs[0].entity_type == kind


def test_missing_required_source_data_fails_instead_of_fabricating():
    with pytest.raises(ValueError):
        normalize(resource(data={"data": {"Ahri": {"name": "Ahri"}}}))


def test_long_descriptions_are_split_without_losing_the_tail():
    payload = resource(
        kind="item",
        data={
            "data": {
                "1001": {
                    "name": "Objet test",
                    "description": "Phrase de test. " * 100 + "Fin unique.",
                }
            }
        },
    )
    docs = normalize(payload)
    assert len(docs) > 1
    assert "Fin unique." in docs[-1].text
    assert all(doc.entity_id == "1001" for doc in docs)
    assert len({doc.id for doc in docs}) == len(docs)
