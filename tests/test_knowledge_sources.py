import json
from unittest.mock import Mock

import pytest

from nexusmind.infrastructure.knowledge_sources import (
    CommunityDragonSource,
    RiotGuideSource,
    WikiSource,
    import_articles,
)


def response(body, status=200):
    content = (body if isinstance(body, str) else json.dumps(body)).encode()
    return Mock(status_code=status, content=content, headers={})


def test_wiki_collection_stays_disabled_instead_of_changing_identity():
    session = Mock()
    with pytest.raises(RuntimeError, match="disabled"):
        list(WikiSource(session=session).collect(["Farming"]))
    session.get.assert_not_called()


def test_client_source_preserves_patch_language_and_does_not_resolve_placeholders():
    session = Mock()
    session.get.side_effect = [
        response("", 404),
        response(
            {
                "id": 103,
                "alias": "Ahri",
                "name": "Ahri",
                "passive": {"name": "Passif", "description": "Soigne Ahri."},
                "spells": [
                    {
                        "spellKey": "q",
                        "name": "Orbe",
                        "description": "Revient.",
                        "dynamicDescription": "Inflige @TotalDamage@ dégâts.",
                        "cooldownCoefficients": [7, 7, 7, 7, 7, 7],
                    }
                ],
            }
        ),
    ]
    articles = list(
        CommunityDragonSource(session=session).collect(
            patch="16.21", locale="fr_FR", champions=[103]
        )
    )
    assert articles[0].patch == "16.21" and articles[0].locale == "fr_FR"
    text = " ".join(p.text for p in articles[0].documents())
    assert "@TotalDamage@" in text and "7" not in text
    assert articles[0].source_revision.startswith("sha256:")
    assert articles[0].license_name and articles[0].attribution
    assert "/16.21/" in articles[0].source_url
    assert session.get.call_args.kwargs["allow_redirects"] is False


@pytest.mark.parametrize("status", [403, 429, 500])
def test_blocked_source_is_not_retried(status):
    session = Mock()
    session.get.return_value = response("blocked", status)
    with pytest.raises(RuntimeError):
        list(
            CommunityDragonSource(session=session).collect(
                patch="16.21", locale="fr_FR", champions=[103]
            )
        )
    session.get.assert_called_once()


def test_robot_disallow_prevents_data_request():
    session = Mock()
    session.get.return_value = response("User-agent: *\nDisallow: /")
    with pytest.raises(RuntimeError, match="robots"):
        list(
            CommunityDragonSource(session=session).collect(
                patch="16.21", locale="fr_FR", champions=[103]
            )
        )
    session.get.assert_called_once()


def test_unpinned_client_patch_is_rejected_before_network():
    session = Mock()
    with pytest.raises(ValueError):
        list(
            CommunityDragonSource(session=session).collect(
                patch="latest", locale="fr_FR", champions=[103]
            )
        )
    session.get.assert_not_called()


def test_riot_guide_extracts_hidden_tabs_but_not_marketing():
    page = {
        "props": {
            "pageProps": {
                "page": {
                    "locale": "fr-fr",
                    "blades": [
                        {
                            "fragmentId": "lol_howtoplay_blade06",
                            "header": {
                                "title": "Se frayer un chemin",
                                "description": {"body": "<p>Des défenses.</p>"},
                            },
                            "groups": [
                                {
                                    "content": {
                                        "title": "Tourelles",
                                        "description": {
                                            "body": "<p>Attaquez avec des <b>sbires</b>.</p>"
                                        },
                                    }
                                },
                                {
                                    "content": {
                                        "title": "Inhibiteurs",
                                        "description": {"body": "<p>Libère des super-sbires.</p>"},
                                    }
                                },
                            ],
                        },
                        {
                            "fragmentId": "lol_howtoplay_blade11",
                            "item": {"title": "Cadeaux", "description": {"body": "Marketing"}},
                        },
                    ],
                }
            }
        }
    }
    session = Mock()
    session.get.side_effect = [
        response("User-agent: *\nAllow: /"),
        response(
            '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(page) + "</script>"
        ),
    ]
    articles = list(RiotGuideSource(session=session).collect())
    assert len(articles) == 1 and articles[0].patch == "unversioned"
    text = " ".join(p.text for p in articles[0].documents())
    assert "super-sbires" in text and "Marketing" not in text and "<b>" not in text


def test_import_rejects_missing_attribution_and_does_not_fetch_urls(tmp_path):
    path = tmp_path / "article.json"
    path.write_text('[{"title":"guide"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        import_articles(path)
