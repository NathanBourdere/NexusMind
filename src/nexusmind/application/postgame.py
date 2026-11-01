"""Post-game Analyst: bounded collection, measurements, no LLM or persistence."""

from datetime import UTC, datetime
from typing import Protocol

from nexusmind.domain.postgame import (
    REGIONS,
    PostGameReport,
    PostGameRequest,
    RiotLiveError,
    analyze_match,
)


class MatchSource(Protocol):
    def account(self, riot_id: str, region: str) -> dict: ...
    def matches(self, puuid: str, region: str) -> list[str]: ...
    def match(self, match_id: str, region: str) -> dict: ...
    def timeline(self, match_id: str, region: str) -> dict: ...


class PostGameAnalyst:
    def __init__(self, source: MatchSource, *, now=lambda: datetime.now(UTC).isoformat()):
        self.source = source
        self.now = now

    def analyze(self, request: PostGameRequest) -> PostGameReport:
        platform, region = REGIONS[request.region]
        try:
            account = self.source.account(request.riot_id, region)
            puuid = account["puuid"]
            if not isinstance(puuid, str) or not puuid:
                raise ValueError("Missing player identity")
            match_id = request.match_id
            if match_id is None:
                matches = self.source.matches(puuid, region)
                if not isinstance(matches, list):
                    raise ValueError("Invalid match list")
                if not matches:
                    return PostGameReport(status="no_matches")
                match_id = matches[0]
            checked = PostGameRequest(
                riot_id=request.riot_id, region=request.region, match_id=match_id
            )
            match = self.source.match(checked.match_id, region)
            if match["metadata"]["matchId"] != checked.match_id:
                raise ValueError("Match response does not match request")
            try:
                timeline = self.source.timeline(checked.match_id, region)
            except RiotLiveError as exc:
                if exc.kind != "not_found":
                    raise
                timeline = None
            return analyze_match(match, timeline, puuid, region=region, collected_at=self.now())
        except RiotLiveError as exc:
            return PostGameReport(
                status=exc.kind, retry_after=exc.retry_after, error_type=type(exc).__name__
            )
        except (ValueError, KeyError, TypeError):
            return PostGameReport(
                status="unavailable",
                error_type="InvalidMatchData",
                limitations=["Les données reçues ne permettent pas une analyse fiable."],
            )
