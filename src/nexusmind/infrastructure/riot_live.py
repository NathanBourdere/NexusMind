"""Account-v1 and Match-v5 over regional HTTPS, with no secret in URLs/errors."""

import math
import time
from urllib.parse import quote

import requests

from nexusmind.domain.postgame import RiotLiveError


class RiotMatchSource:
    def __init__(self, api_key: str, *, session=None, clock=time.monotonic):
        if not api_key.strip():
            raise ValueError("RIOT_API_KEY is required")
        self._key = api_key
        self.session = session if session is not None else requests.Session()
        self._owns_session = session is None
        self.clock = clock
        self.retry_until = 0

    def close(self):
        if self._owns_session:
            self.session.close()

    def _get(self, region, path, params=None):
        if region not in {"europe", "americas", "asia", "sea"}:
            raise ValueError("Invalid regional routing")
        if self.clock() < self.retry_until:
            raise RiotLiveError("rate_limited", retry_after=self.retry_until - self.clock())
        try:
            response = self.session.get(
                f"https://{region}.api.riotgames.com{path}",
                params=params,
                headers={"X-Riot-Token": self._key},
                timeout=(5, 20),
                allow_redirects=False,
            )
        except requests.RequestException:
            raise RiotLiveError("unavailable") from None
        status = response.status_code
        if status == 429:
            try:
                delay = float(response.headers.get("Retry-After", "60"))
                if not math.isfinite(delay) or delay < 0:
                    raise ValueError
            except (ValueError, TypeError):
                delay = 60
            self.retry_until = self.clock() + delay
            raise RiotLiveError("rate_limited", status_code=429, retry_after=delay)
        if status in (401, 403):
            raise RiotLiveError("authentication_failed", status_code=status)
        if status == 404:
            raise RiotLiveError("not_found", status_code=404)
        if status != 200:
            raise RiotLiveError("unavailable", status_code=status)
        try:
            return response.json()
        except ValueError:
            raise RiotLiveError("unavailable", status_code=200) from None

    def account(self, riot_id, region):
        name, tag = riot_id.split("#")
        return self._get(
            region,
            f"/riot/account/v1/accounts/by-riot-id/{quote(name, safe='')}/{quote(tag, safe='')}",
        )

    def matches(self, puuid, region):
        return self._get(
            region,
            f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids",
            {"start": 0, "count": 1},
        )

    def match(self, match_id, region):
        return self._get(region, f"/lol/match/v5/matches/{quote(match_id, safe='')}")

    def timeline(self, match_id, region):
        return self._get(region, f"/lol/match/v5/matches/{quote(match_id, safe='')}/timeline")
