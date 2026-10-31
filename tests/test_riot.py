from unittest.mock import Mock

import pytest
import requests

from nexusmind.infrastructure.riot import RiotError, RiotSource


def response(status=200, data=None, headers=None):
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = data
    return result


def test_retries_rate_limit_with_timeout_and_bounded_wait():
    session = Mock()
    session.get.side_effect = [
        response(429, headers={"Retry-After": "2"}),
        response(data=["16.1.1"]),
    ]
    sleep = Mock()
    source = RiotSource(session=session, sleep=sleep, retries=1, timeout=9)
    assert source.resolve_patch(None) == "16.1.1"
    sleep.assert_called_once_with(2.0)
    assert session.get.call_args.kwargs["timeout"] == 9


@pytest.mark.parametrize("status", [401, 403, 404])
def test_permanent_errors_are_not_retried(status):
    session = Mock()
    session.get.return_value = response(status)
    with pytest.raises(RiotError):
        RiotSource(session=session).resolve_patch(None)
    assert session.get.call_count == 1


def test_network_failures_are_bounded():
    session = Mock()
    session.get.side_effect = requests.Timeout("offline")
    with pytest.raises(RiotError):
        RiotSource(session=session, sleep=Mock(), retries=2).resolve_patch(None)
    assert session.get.call_count == 3


def test_collect_uses_only_riot_and_resolves_canonical_champion_id():
    session = Mock()
    session.get.side_effect = [
        response(data={"data": {"Ahri": {"id": "Ahri", "name": "Ahri"}}}),
        response(data={"data": {"Ahri": {"id": "Ahri"}}}),
    ]
    source = RiotSource(session=session)
    resources = list(source.collect("16.1.1", "fr_FR", ["champion"], ["ahri"]))
    assert len(resources) == 1
    assert resources[0]["source_url"].endswith("champion/Ahri.json")
    assert all(
        call.args[0].startswith("https://ddragon.leagueoflegends.com/")
        for call in session.get.call_args_list
    )


def test_unknown_champion_fails_before_partial_collection():
    session = Mock()
    session.get.return_value = response(data={"data": {"Ahri": {"id": "Ahri", "name": "Ahri"}}})
    with pytest.raises(RiotError, match="Unknown champion"):
        list(RiotSource(session=session).collect("16.1.1", "fr_FR", ["champion"], ["missing"]))
