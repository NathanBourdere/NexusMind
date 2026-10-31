"""Bounded public Data Dragon access. No API key and no third-party fallback."""

import re
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Any

import requests

BASE = "https://ddragon.leagueoflegends.com"
KINDS = ("champion", "item", "rune", "summoner_spell")


class RiotError(RuntimeError):
    """An upstream failure, distinct from an empty search result."""


class RiotSource:
    def __init__(
        self,
        session=None,
        sleep: Callable = time.sleep,
        retries: int = 2,
        timeout: float = 20,
        max_retry_after: float = 60,
    ):
        if retries < 0 or timeout <= 0:
            raise ValueError("Invalid retry or timeout configuration")
        self.session = session if session is not None else requests.Session()
        self._owns_session = session is None
        self.sleep = sleep
        self.retries = retries
        self.timeout = timeout
        self.max_retry_after = max_retry_after

    def close(self):
        if self._owns_session:
            self.session.close()

    def _get(self, url: str) -> Any:
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt == self.retries:
                    raise RiotError(f"Riot request failed: {url}") from exc
                self.sleep(2**attempt)
                continue
            status = response.status_code
            if status == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    raise RiotError(f"Invalid Riot JSON: {url}") from exc
            if status != 429 and status < 500:
                raise RiotError(f"Riot HTTP {status}: {url}")
            if attempt == self.retries:
                raise RiotError(f"Riot retry budget exhausted (HTTP {status}): {url}")
            try:
                delay = float(response.headers.get("Retry-After", 2**attempt))
            except ValueError as exc:
                raise RiotError("Invalid Riot Retry-After header") from exc
            # Fail instead of retrying earlier than Riot permits or sleeping indefinitely.
            if not 0 <= delay <= self.max_retry_after:
                raise RiotError("Riot Retry-After exceeds this run's wait budget")
            self.sleep(delay)
        raise AssertionError("Unreachable")

    def resolve_patch(self, patch: str | None) -> str:
        if patch is None:
            versions = self._get(f"{BASE}/api/versions.json")
            if not isinstance(versions, list) or not versions:
                raise RiotError("Riot returned no versions")
            patch = versions[0]
        if not isinstance(patch, str) or not re.fullmatch(r"\d+\.\d+\.\d+", patch):
            raise ValueError("Patch must be a Data Dragon version, e.g. 16.1.1")
        return patch

    def collect(
        self, patch: str, locale: str, kinds: list[str], champions: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        self.resolve_patch(patch)
        if not re.fullmatch(r"[a-z]{2}_[A-Z]{2}", locale):
            raise ValueError("Locale must use the format fr_FR")
        if not kinds or set(kinds) - set(KINDS):
            raise ValueError(f"Resource kinds must be selected from {KINDS}")
        prefix = f"{BASE}/cdn/{patch}/data/{locale}"

        def resource(kind, endpoint):
            url = f"{prefix}/{endpoint}"
            return {
                "kind": kind,
                "patch": patch,
                "locale": locale,
                "source_url": url,
                "retrieved_at": datetime.now(UTC).isoformat(),
                "data": self._get(url),
            }

        if "champion" in kinds:
            listing = self._get(f"{prefix}/champion.json")["data"]
            aliases = {
                alias.casefold(): key
                for key, value in listing.items()
                for alias in (key, value["name"])
            }
            selected = sorted(listing) if not champions else []
            for name in champions or []:
                if name.casefold() not in aliases:
                    raise RiotError(f"Unknown champion: {name}")
                selected.append(aliases[name.casefold()])
            for champion in dict.fromkeys(selected):
                yield resource("champion", f"champion/{champion}.json")
        for kind, endpoint in (
            ("item", "item.json"),
            ("rune", "runesReforged.json"),
            ("summoner_spell", "summoner.json"),
        ):
            if kind in kinds:
                yield resource(kind, endpoint)
