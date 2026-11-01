"""Bounded, explicit public sources; no login, crawl or identity rotation."""

import hashlib
import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.robotparser import RobotFileParser

import requests

from nexusmind.domain.documents import clean
from nexusmind.domain.knowledge import SourceArticle

USER_AGENT = "NexusMind/0.1 (+https://github.com/NathanBourdere/NexusMind)"
RIOT_RIGHTS = "https://www.riotgames.com/en/legal"


class WikiSource:
    def __init__(self, session=None):
        self.session = session

    def collect(self, pages):
        raise RuntimeError("Wiki collection disabled: robots excludes AI bots and API paths")


class PublicSource:
    base_url: str

    def __init__(self, session=None):
        self.session = session if session is not None else requests.Session()
        self.owns_session = session is None
        self.robots = None

    def close(self):
        if self.owns_session:
            self.session.close()

    def _request(self, url, *, robots=False):
        try:
            response = self.session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=(5, 20),
                allow_redirects=False,
            )
        except requests.RequestException:
            raise RuntimeError("Public source transport unavailable") from None
        if robots and response.status_code == 404:
            return b"User-agent: *\nAllow: /"
        if response.status_code != 200:
            retry = response.headers.get("Retry-After", "unspecified")
            raise RuntimeError(f"Public source HTTP {response.status_code}; Retry-After={retry}")
        if len(response.content) > 4_000_000:
            raise ValueError("Source response exceeds 4 MB")
        return response.content

    def read(self, path):
        url = self.base_url + path
        if self.robots is None:
            self.robots = RobotFileParser()
            self.robots.parse(
                self._request(self.base_url + "/robots.txt", robots=True)
                .decode("utf-8")
                .splitlines()
            )
        if not self.robots.can_fetch(USER_AGENT, url):
            raise RuntimeError("Access refused by source robots.txt")
        return self._request(url)


def revision(payload):
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
    )


class CommunityDragonSource(PublicSource):
    base_url = "https://raw.communitydragon.org"

    def collect(self, *, patch, locale, champions):
        if not re.fullmatch(r"\d+\.\d+", patch):
            raise ValueError("CommunityDragon requires a pinned major.minor patch")
        if locale not in {"fr_FR", "en_US"}:
            raise ValueError("CommunityDragon locales supported: fr_FR, en_US")
        if (
            not champions
            or len(champions) > 200
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value <= 0
                for value in champions
            )
        ):
            raise ValueError("Provide 1..200 positive numeric champion IDs")
        for champion in dict.fromkeys(champions):
            language = "default" if locale == "en_US" else locale.lower()
            path = (
                f"/{patch}/plugins/rcp-be-lol-game-data/global/{language}"
                f"/v1/champions/{champion}.json"
            )
            data = json.loads(self.read(path))
            if data["id"] != champion:
                raise ValueError("CommunityDragon champion ID mismatch")
            sections = {}
            passive = data["passive"]
            sections[f"Passif — {passive['name']}"] = clean(passive["description"])
            for spell in data["spells"]:
                heading = f"{spell['spellKey'].upper()} — {spell['name']}"
                text = clean(spell["description"])
                dynamic = clean(spell.get("dynamicDescription", ""))
                if dynamic and dynamic != text:
                    text += " Texte client non résolu : " + dynamic
                sections[heading] = text
            yield SourceArticle(
                source_id="communitydragon",
                source_key=f"champion-{champion}",
                source_name="CommunityDragon — données client Riot",
                source_url=self.base_url + path,
                source_revision=revision(data),
                title=data["name"],
                locale=locale,
                patch=patch,
                license_name="Riot Games — Legal Jibber Jabber (assets)",
                license_url=RIOT_RIGHTS,
                attribution="Données Riot Games, distribuées par CommunityDragon. "
                "Projet communautaire non affilié à Riot Games.",
                retrieved_at=datetime.now(UTC).isoformat(),
                topics=[data["name"], data["alias"]],
                sections=sections,
            )


class NextData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "__NEXT_DATA__":
            self.active = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


GUIDE_TOPICS = {
    "lol_howtoplay_blade05": ["nexus", "base", "fontaine"],
    "lol_howtoplay_blade06": [
        "tourelle",
        "tourelles",
        "tour",
        "tours",
        "inhibiteur",
        "inhibiteurs",
        "super sbires",
        "siege",
    ],
    "lol_howtoplay_blade07": ["jungle", "baron", "nashor", "dragon", "dragons"],
    "lol_howtoplay_blade08": [
        "role",
        "roles",
        "poste",
        "postes",
        "support",
        "voie du bas",
        "voie du haut",
        "voie du milieu",
    ],
    "lol_howtoplay_blade09": ["experience", "xp", "or", "economie", "niveau", "niveaux"],
    "lol_howtoplay_blade10": ["competences", "sorts d invocateur", "objets"],
}


class RiotGuideSource(PublicSource):
    base_url = "https://www.leagueoflegends.com"

    def collect(self):
        path = "/fr-fr/how-to-play/"
        parser = NextData()
        parser.feed(self.read(path).decode("utf-8"))
        page = json.loads("".join(parser.parts))["props"]["pageProps"]["page"]
        if page["locale"] != "fr-fr":
            raise ValueError("Unexpected Riot guide language")
        count = 0
        for blade in page["blades"]:
            key = blade.get("fragmentId")
            if key not in GUIDE_TOPICS:
                continue
            header = blade["header"]
            sections = {header["title"]: clean(header["description"]["body"])}
            for group in blade.get("groups", []):
                content = group["content"]
                heading = content.get("title") or group["label"]
                sections[heading] = clean(content["description"]["body"])
            yield SourceArticle(
                source_id="riot-guide",
                source_key=key,
                source_name="Riot Games — Comment jouer",
                source_url=self.base_url + path + "#" + key,
                source_revision=revision(sections),
                title=header["title"],
                locale="fr_FR",
                license_name="Riot Games — Legal Jibber Jabber",
                license_url=RIOT_RIGHTS,
                attribution="Riot Games, League of Legends — guide Comment jouer.",
                retrieved_at=datetime.now(UTC).isoformat(),
                topics=GUIDE_TOPICS[key],
                sections=sections,
            )
            count += 1
        if not count:
            raise ValueError("Riot guide layout changed; no approved sections found")


def import_articles(path: Path) -> list[SourceArticle]:
    if path.stat().st_size > 4_000_000:
        raise ValueError("Import exceeds 4 MB")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not 1 <= len(data) <= 200:
        raise ValueError("Import must contain 1..200 source articles")
    return [SourceArticle.model_validate(article) for article in data]
