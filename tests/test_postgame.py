from copy import deepcopy

from nexusmind.domain.postgame import analyze_match


def match_fixture():
    players = []
    for i in range(1, 11):
        players.append(
            {
                "puuid": f"synthetic-player-{i}",
                "participantId": i,
                "teamId": 100 if i <= 5 else 200,
                "championName": "Ahri" if i == 1 else "Synthetic",
                "teamPosition": "MIDDLE" if i in (1, 6) else "TOP",
                "kills": 4,
                "deaths": 2,
                "assists": 6,
                "totalMinionsKilled": 100,
                "neutralMinionsKilled": 20,
                "goldEarned": 9000,
                "visionScore": 12,
                "totalDamageDealtToChampions": 12000,
                "win": i <= 5,
            }
        )
    return {
        "metadata": {"matchId": "EUW1_123"},
        "info": {
            "gameVersion": "16.21.1.123",
            "gameDuration": 1200,
            "mapId": 11,
            "queueId": 420,
            "participants": players,
        },
    }


def timeline_fixture():
    return {
        "metadata": {"matchId": "EUW1_123"},
        "info": {
            "frames": [
                {
                    "timestamp": 600000,
                    "participantFrames": {
                        "1": {"totalGold": 4500, "minionsKilled": 65, "jungleMinionsKilled": 5},
                        "6": {"totalGold": 5000, "minionsKilled": 72, "jungleMinionsKilled": 8},
                    },
                    "events": [],
                },
                {
                    "timestamp": 900000,
                    "participantFrames": {},
                    "events": [
                        {"type": "CHAMPION_KILL", "timestamp": 800000, "victimId": 1},
                        {
                            "type": "ELITE_MONSTER_KILL",
                            "timestamp": 850000,
                            "killerTeamId": 200,
                            "monsterType": "DRAGON",
                        },
                        {
                            "type": "ELITE_MONSTER_KILL",
                            "timestamp": 910000,
                            "killerTeamId": 200,
                            "monsterType": "BARON_NASHOR",
                        },
                    ],
                },
            ]
        },
    }


def run(match=None, timeline=None):
    return analyze_match(
        match or match_fixture(),
        timeline if timeline is not None else timeline_fixture(),
        "synthetic-player-1",
        region="europe",
        collected_at="2026-11-01T12:00:00+00:00",
    )


def test_metrics_are_computed_with_explicit_units_and_real_denominators():
    result = run()
    assert result.status == "ok"
    assert result.metrics["cs_per_minute"].value == 6
    assert result.metrics["kill_participation_percent"].value == 50
    assert result.metrics["kda"].value == 5
    assert result.metrics["gold_difference_near_10m"].value == -500
    assert result.metrics["cs_difference_near_10m"].value == -10
    assert result.metrics["enemy_objectives_after_death"].value == 1
    assert result.game_version == "16.21.1.123"
    assert "synthetic-player" not in result.model_dump_json()
    assert result.sources and result.recommendations


def test_missing_values_and_zero_denominators_remain_absent():
    match = deepcopy(match_fixture())
    player = match["info"]["participants"][0]
    player.pop("visionScore")
    player["deaths"] = 0
    result = run(match)
    assert result.metrics["vision_score"].value is None
    assert result.metrics["kda"].value is None


def test_no_timeline_is_partial_and_does_not_invent_snapshots():
    result = analyze_match(
        match_fixture(),
        None,
        "synthetic-player-1",
        region="europe",
        collected_at="2026-11-01T12:00:00+00:00",
    )
    assert result.status == "partial"
    assert result.metrics["gold_difference_near_10m"].value is None
    assert result.metrics["enemy_objectives_after_death"].value is None


def test_unknown_role_does_not_guess_a_lane_opponent():
    match = match_fixture()
    match["info"]["participants"][0]["teamPosition"] = "INVALID"
    result = run(match)
    assert result.role is None
    assert result.metrics["gold_difference_near_10m"].value is None
