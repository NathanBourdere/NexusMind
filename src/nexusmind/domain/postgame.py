"""Post-game contracts and deterministic measurements."""

import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

REGIONS = {
    "EUW": ("euw1", "europe"),
    "EUNE": ("eun1", "europe"),
    "TR": ("tr1", "europe"),
    "RU": ("ru", "europe"),
    "NA": ("na1", "americas"),
    "BR": ("br1", "americas"),
    "LAN": ("la1", "americas"),
    "LAS": ("la2", "americas"),
    "KR": ("kr", "asia"),
    "JP": ("jp1", "asia"),
    "OCE": ("oc1", "sea"),
    "SEA": ("sg2", "sea"),
}


class PostGameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    riot_id: str = Field(min_length=3, max_length=100)
    region: str = "EUW"
    match_id: str | None = Field(default=None, pattern=r"^[A-Z0-9]+_[0-9]+$")

    @model_validator(mode="after")
    def validate_identity(self):
        self.region = self.region.upper()
        if self.region not in REGIONS:
            raise ValueError("Unsupported region")
        parts = self.riot_id.split("#")
        if len(parts) != 2 or not all(part.strip() for part in parts):
            raise ValueError("Riot ID must use Name#TAG")
        prefix = REGIONS[self.region][0].upper() + "_"
        if self.match_id and not self.match_id.startswith(prefix):
            raise ValueError("Match does not belong to the selected platform")
        return self


class RiotLiveError(RuntimeError):
    def __init__(self, kind: str, *, status_code=None, retry_after=None):
        super().__init__(f"Riot service: {kind}")
        self.kind, self.status_code, self.retry_after = kind, status_code, retry_after


class Metric(BaseModel):
    value: float | None = Field(allow_inf_nan=False)
    unit: str
    origin: Literal["riot", "computed"] = "computed"
    formula: str | None = None
    timestamp_ms: int | None = None


class PostGameReport(BaseModel):
    status: Literal[
        "ok",
        "partial",
        "no_matches",
        "not_found",
        "authentication_failed",
        "rate_limited",
        "unavailable",
    ]
    match_id: str | None = None
    game_version: str | None = None
    champion: str | None = None
    role: str | None = None
    won: bool | None = None
    metrics: dict[str, Metric] = Field(default_factory=dict)
    death_timestamps_ms: list[int] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    retry_after: float | None = None
    error_type: str | None = None


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def total(*values):
    return sum(values) if all(value is not None for value in values) else None


def ratio(numerator, denominator, scale=1):
    return (
        round(numerator / denominator * scale, 3)
        if (numerator is not None and denominator is not None and denominator > 0)
        else None
    )


def analyze_match(match, timeline, puuid, *, region, collected_at):
    try:
        info, match_id = match["info"], match["metadata"]["matchId"]
        players = info["participants"]
        selected = [p for p in players if p.get("puuid") == puuid]
        if len(selected) != 1:
            raise ValueError("Selected player is absent or duplicated")
        player = selected[0]
        version = info.get("gameVersion")
        if not isinstance(version, str) or not re.match(r"^(1[2-9]|[2-9][0-9])\.", version):
            raise ValueError("Only modern Match-v5 durations are supported")
        duration = number(info.get("gameDuration"))
        team = player.get("teamId")
        if team not in (100, 200):
            raise ValueError("Missing team identity")
        role = player.get("teamPosition")
        role = role if role in {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"} else None
        kills, assists, deaths = (number(player.get(k)) for k in ("kills", "assists", "deaths"))
        cs = total(
            number(player.get("totalMinionsKilled")), number(player.get("neutralMinionsKilled"))
        )
        team_kills = total(*(number(p.get("kills")) for p in players if p.get("teamId") == team))
        metrics = {
            "duration": Metric(value=duration, unit="seconds", origin="riot"),
            "kills": Metric(value=kills, unit="kills", origin="riot"),
            "deaths": Metric(value=deaths, unit="deaths", origin="riot"),
            "assists": Metric(value=assists, unit="assists", origin="riot"),
            "cs": Metric(value=cs, unit="minions", formula="lane minions + neutral minions"),
            "cs_per_minute": Metric(
                value=ratio(cs, duration, 60),
                unit="minions/minute",
                formula="CS / gameDuration_seconds * 60",
            ),
            "kda": Metric(
                value=ratio(total(kills, assists), deaths),
                unit="ratio",
                formula="(kills + assists) / deaths; undefined for zero deaths",
            ),
            "kill_participation_percent": Metric(
                value=ratio(total(kills, assists), team_kills, 100),
                unit="percent",
                formula="(kills + assists) / sum(team kills) * 100",
            ),
        }
        for key, field, unit in [
            ("gold_earned", "goldEarned", "gold"),
            ("vision_score", "visionScore", "score"),
            ("champion_damage", "totalDamageDealtToChampions", "damage"),
        ]:
            metrics[key] = Metric(value=number(player.get(field)), unit=unit, origin="riot")
        for key, unit in [
            ("gold_difference_near_10m", "gold"),
            ("cs_difference_near_10m", "minions"),
            ("enemy_objectives_after_death", "events"),
        ]:
            metrics[key] = Metric(value=None, unit=unit)
        result = PostGameReport(
            status="partial" if timeline is None else "ok",
            match_id=match_id,
            game_version=version,
            champion=player.get("championName"),
            role=role,
            won=player.get("win") if isinstance(player.get("win"), bool) else None,
            metrics=metrics,
            sources=[
                {
                    "source": "Riot Match-v5",
                    "endpoint": f"https://{region}.api.riotgames.com/lol/match/v5/matches/{{matchId}}",
                    "retrieved_at": collected_at,
                    "game_version": version,
                    "locale": None,
                }
            ],
            limitations=[
                "Une seule partie ne mesure pas ton niveau global.",
                "Les conseils sont des hypothèses ; aucune causalité de défaite n'est déduite.",
                "Une valeur absente ou un ratio non défini reste absent.",
            ],
        )
        metrics = result.metrics
        if timeline is not None:
            add_timeline(result, timeline, players, player, region, collected_at)
        else:
            result.limitations.append("Timeline absente : aucun écart ou événement n'est inventé.")
        if (
            role in {"TOP", "MIDDLE", "BOTTOM", "JUNGLE"}
            and metrics["cs_per_minute"].value is not None
        ):
            result.recommendations.append(
                f"Hypothèse de progression : avec {metrics['cs_per_minute'].value} CS/min, "
                "revois deux retours à la base et les ressources non prises, sans seuil universel."
            )
        if metrics["vision_score"].value is not None:
            result.recommendations.append(
                f"Hypothèse de progression : score de vision {metrics['vision_score'].value}. "
                "Revois deux placements de balises avant un objectif ; "
                "le score seul ne juge pas leur qualité."
            )
        if result.death_timestamps_ms:
            result.recommendations.append(
                "Hypothèse de progression : revois la minute avant chaque mort et les 90 secondes "
                "suivantes, en distinguant tes choix, la vision et les décisions adverses."
            )
        if metrics["enemy_objectives_after_death"].value:
            result.limitations.append(
                "Un objectif après une mort ne prouve pas un lien de causalité."
            )
        return result
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ValueError("Malformed or incompatible Match-v5 data") from exc


def add_timeline(result, timeline, players, player, region, collected_at):
    if timeline["metadata"]["matchId"] != result.match_id:
        raise ValueError("Timeline does not match game")
    frames = timeline["info"]["frames"]
    if not isinstance(frames, list) or not frames:
        raise ValueError("Timeline has no frames")
    if any(not isinstance(frame.get("events"), list) for frame in frames):
        raise ValueError("Timeline event data is missing")
    participant, team = player["participantId"], player["teamId"]
    events = [event for frame in frames for event in frame.get("events", [])]
    result.death_timestamps_ms = sorted(
        {
            int(e["timestamp"])
            for e in events
            if e.get("type") == "CHAMPION_KILL"
            and e.get("victimId") == participant
            and number(e.get("timestamp")) is not None
        }
    )
    objectives = [
        e
        for e in events
        if e.get("type") == "ELITE_MONSTER_KILL"
        and e.get("killerTeamId") == 300 - team
        and number(e.get("timestamp")) is not None
    ]
    count = sum(
        any(0 <= e["timestamp"] - death <= 90000 for death in result.death_timestamps_ms)
        for e in objectives
    )
    result.metrics["enemy_objectives_after_death"] = Metric(
        value=count,
        unit="events",
        formula="enemy ELITE_MONSTER_KILL events within 0..90 seconds after a recorded death",
    )
    snapshots = [
        f
        for f in frames
        if number(f.get("timestamp")) is not None and abs(f["timestamp"] - 600000) <= 30000
    ]
    opponents = (
        [p for p in players if p.get("teamId") != team and p.get("teamPosition") == result.role]
        if result.role
        else []
    )
    if snapshots and len(opponents) == 1:
        snapshot = min(snapshots, key=lambda f: abs(f["timestamp"] - 600000))
        own = snapshot.get("participantFrames", {}).get(str(participant), {})
        other = snapshot.get("participantFrames", {}).get(str(opponents[0]["participantId"]), {})
        values = [
            (
                "gold_difference_near_10m",
                number(own.get("totalGold")),
                number(other.get("totalGold")),
                "gold",
            ),
            (
                "cs_difference_near_10m",
                total(number(own.get("minionsKilled")), number(own.get("jungleMinionsKilled"))),
                total(number(other.get("minionsKilled")), number(other.get("jungleMinionsKilled"))),
                "minions",
            ),
        ]
        for key, left, right, unit in values:
            result.metrics[key] = Metric(
                value=left - right if left is not None and right is not None else None,
                unit=unit,
                timestamp_ms=int(snapshot["timestamp"]),
                formula="player - unique enemy with same Riot teamPosition",
            )
    result.sources.append(
        {
            "source": "Riot Match-v5 timeline",
            "endpoint": f"https://{region}.api.riotgames.com/lol/match/v5/matches/{{matchId}}/timeline",
            "retrieved_at": collected_at,
            "game_version": result.game_version,
            "locale": None,
        }
    )
