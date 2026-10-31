"""Searchable passages from official payloads, independent of historical schemas."""

import hashlib
import json
import re
import textwrap
import uuid
from html import unescape
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    entity_type: str
    entity_id: str
    section: str
    text: str = Field(min_length=1)
    patch: str
    locale: str
    source_url: str
    retrieved_at: str
    content_hash: str
    source_name: str = "Riot Data Dragon"
    schema_version: int = 1


def clean(value: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", value)).split())


def normalize(resource: dict[str, Any]) -> list[Document]:
    """Reject malformed source fields rather than inventing missing game facts."""
    try:
        kind = resource["kind"]
        data = resource["data"]
        passages: list[tuple[str, str, str]] = []
        if kind == "rune":
            for tree in data:
                for slot in tree["slots"]:
                    for rune in slot["runes"]:
                        passages.append(
                            (str(rune["id"]), "description", f"{rune['name']}. {rune['longDesc']}")
                        )
        elif kind in {"champion", "item", "summoner_spell"}:
            for key, entity in data["data"].items():
                entity_id = str(entity.get("id", key))
                name = entity["name"]
                if kind == "champion":
                    passages.append(
                        (
                            entity_id,
                            "overview",
                            f"{name}, {entity['title']}. Classes: {', '.join(entity['tags'])}.",
                        )
                    )
                    passive = entity["passive"]
                    passages.append(
                        (
                            entity_id,
                            "passive",
                            f"{name} — {passive['name']}. {passive['description']}",
                        )
                    )
                    for spell in entity["spells"]:
                        passages.append(
                            (
                                entity_id,
                                f"spell:{spell['id']}",
                                f"{name} — {spell['name']}. {spell['description']}",
                            )
                        )
                else:
                    text = f"{name}. {entity['description']}"
                    for field in ("gold", "stats", "maps", "cooldown", "cost", "range"):
                        if field in entity:
                            text += f" {field}: {json.dumps(entity[field], ensure_ascii=False)}."
                    passages.append((entity_id, "description", text))
        else:
            raise ValueError(f"Unsupported resource kind: {kind}")
        if not passages:
            raise ValueError(f"Empty resource: {kind}")
        documents = []
        for entity_id, section, raw_text in passages:
            text = clean(raw_text)
            chunks = textwrap.wrap(text, width=400, break_on_hyphens=False)
            for index, chunk in enumerate(chunks):
                chunk_section = section if len(chunks) == 1 else f"{section}:chunk:{index}"
                if len(chunks) > 1:
                    chunk = f"{entity_id} / {section}. {chunk}"
                identity = [kind, entity_id, chunk_section, resource["patch"], resource["locale"]]
                documents.append(
                    Document(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(identity))),
                        entity_type=kind,
                        entity_id=entity_id,
                        section=chunk_section,
                        text=chunk,
                        patch=resource["patch"],
                        locale=resource["locale"],
                        source_url=resource["source_url"],
                        retrieved_at=resource["retrieved_at"],
                        content_hash=hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                    )
                )
        return documents
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Malformed Riot resource: {exc}") from exc
