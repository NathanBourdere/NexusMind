"""Revisioned source articles, separate from the original Riot-only corpus."""

import hashlib
import json
import textwrap
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from nexusmind.domain.documents import Document


class SourceArticle(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=80)
    source_key: str = Field(min_length=1, max_length=200)
    source_name: str = Field(min_length=1)
    source_url: str = Field(pattern=r"^https://")
    source_revision: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    locale: str = Field(pattern=r"^[a-z]{2}_[A-Z]{2}$")
    patch: str = Field(default="unversioned", pattern=r"^(unversioned|\d+\.\d+(\.\d+)?)$")
    license_name: str = Field(min_length=1)
    license_url: str = Field(pattern=r"^https://")
    attribution: str = Field(min_length=1)
    retrieved_at: str
    topics: list[str] = Field(min_length=1)
    sections: dict[str, str] = Field(min_length=1)

    @field_validator("retrieved_at")
    @classmethod
    def dated(cls, value):
        if datetime.fromisoformat(value).utcoffset() is None:
            raise ValueError("retrieved_at must include a timezone")
        return value

    @field_validator("topics")
    @classmethod
    def useful_topics(cls, values):
        if any(len(value.strip()) < 2 for value in values):
            raise ValueError("Topic aliases must contain at least two characters")
        return [value.strip() for value in values]

    @field_validator("sections")
    @classmethod
    def useful_sections(cls, values):
        if len(values) > 1000 or any(
            not key.strip() or len(key) > 120 or not value.strip() for key, value in values.items()
        ):
            raise ValueError("Sections must have nonempty headings and text")
        return values

    def documents(self) -> list[Document]:
        result = []
        for heading, text in self.sections.items():
            for index, chunk in enumerate(textwrap.wrap(text, width=350, break_on_hyphens=False)):
                text = f"{self.title} / {heading}. {chunk}"
                digest = hashlib.sha256(text.encode()).hexdigest()
                identity = [
                    self.source_id,
                    self.source_key,
                    self.source_revision,
                    self.patch,
                    self.locale,
                    heading,
                    index,
                    digest,
                ]
                result.append(
                    Document(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(identity))),
                        entity_type="concept",
                        entity_id=f"{self.source_id}:{self.source_key}@{self.source_revision}",
                        section=f"{heading}:chunk:{index}",
                        text=text,
                        patch=self.patch,
                        locale=self.locale,
                        source_url=self.source_url,
                        retrieved_at=self.retrieved_at,
                        content_hash=digest,
                        source_name=self.source_name,
                        schema_version=2,
                        source_id=self.source_id,
                        source_revision=self.source_revision,
                        source_key=self.source_key,
                        title=self.title,
                        content_kind="reference",
                        license_name=self.license_name,
                        license_url=self.license_url,
                        attribution=self.attribution,
                        topics=self.topics,
                    )
                )
        if not result:
            raise ValueError("Article has no usable text")
        return result


def compatible_patch(source_patch: str, requested_patch: str) -> bool:
    return source_patch in {"unversioned", requested_patch, requested_patch.rsplit(".", 1)[0]}
