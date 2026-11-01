from unittest.mock import Mock

import pytest
from test_postgame import match_fixture, timeline_fixture

from nexusmind.application.postgame import PostGameAnalyst
from nexusmind.domain.postgame import PostGameRequest, RiotLiveError
from nexusmind.infrastructure.riot_live import RiotMatchSource


def test_regional_routing_and_key_only_in_headers():
    transport = Mock()
    transport.get.return_value.status_code = 200
    transport.get.return_value.json.return_value = {"puuid": "synthetic"}
    source = RiotMatchSource("PRIVATE", session=transport)
    source.account("Synthetic Player#TAG", "europe")
    args, kwargs = transport.get.call_args
    assert (
        args[0]
        == "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Synthetic%20Player/TAG"
    )
    assert "PRIVATE" not in args[0]
    assert kwargs["headers"]["X-Riot-Token"] == "PRIVATE"
    assert kwargs["timeout"] == (5, 20) and not kwargs["allow_redirects"]


def test_rate_limit_stops_and_respects_cooldown_without_sleeping():
    transport = Mock()
    transport.get.return_value.status_code = 429
    transport.get.return_value.headers = {"Retry-After": "12"}
    source = RiotMatchSource("PRIVATE", session=transport, clock=lambda: 100)
    for _ in range(2):
        with pytest.raises(RiotLiveError) as error:
            source.matches("synthetic", "europe")
        assert error.value.kind == "rate_limited"
        assert error.value.retry_after == 12
    transport.get.assert_called_once()


@pytest.mark.parametrize(
    "status,kind", [(403, "authentication_failed"), (404, "not_found"), (500, "unavailable")]
)
def test_failures_are_sanitized_without_retry(status, kind):
    transport = Mock()
    transport.get.return_value.status_code = status
    source = RiotMatchSource("PRIVATE", session=transport)
    with pytest.raises(RiotLiveError) as error:
        source.matches("synthetic", "europe")
    assert error.value.kind == kind and "PRIVATE" not in str(error.value)
    transport.get.assert_called_once()


def test_analyst_collects_one_match_and_does_not_return_player_identifier():
    source = Mock()
    source.account.return_value = {"puuid": "synthetic-player-1"}
    source.matches.return_value = ["EUW1_123"]
    source.match.return_value = match_fixture()
    source.timeline.return_value = timeline_fixture()
    result = PostGameAnalyst(source).analyze(PostGameRequest(riot_id="Synthetic#TEST"))
    assert result.status == "ok"
    assert "synthetic-player" not in result.model_dump_json()
    source.matches.assert_called_once_with("synthetic-player-1", "europe")
    source.timeline.assert_called_once_with("EUW1_123", "europe")


def test_missing_timeline_is_partial_but_outage_is_not_silenced():
    source = Mock()
    source.account.return_value = {"puuid": "synthetic-player-1"}
    source.matches.return_value = ["EUW1_123"]
    source.match.return_value = match_fixture()
    source.timeline.side_effect = RiotLiveError("not_found")
    analyst = PostGameAnalyst(source)
    assert analyst.analyze(PostGameRequest(riot_id="Synthetic#TEST")).status == "partial"
    source.timeline.side_effect = RiotLiveError("unavailable")
    assert analyst.analyze(PostGameRequest(riot_id="Synthetic#TEST")).status == "unavailable"
