"""Retrieval contracts: passages are evidence candidates, never generated answers."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nexusmind.domain.documents import Document

EntityType = Literal["champion", "item", "rune", "summoner_spell"]


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(min_length=1, max_length=2000)
    patch: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    locale: str = Field(default="fr_FR", pattern=r"^[a-z]{2}_[A-Z]{2}$")
    limit: int = Field(default=5, ge=1, le=20)
    entity_type: EntityType | None = None
    entity_ids: list[str] = Field(default_factory=list, max_length=10)
    section: str | None = None


class RetrievalFilters(BaseModel):
    entity_type: EntityType | None = None
    entity_ids: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)


class Passage(Document):
    score: float = Field(allow_inf_nan=False)
    embedding_model: str
    embedding_revision: str


class EntityCandidate(BaseModel):
    entity_type: EntityType
    entity_id: str


class RetrievalResult(BaseModel):
    query: str
    patch: str
    locale: str
    status: Literal["ok", "no_results", "out_of_scope", "needs_clarification", "unavailable"]
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    passages: list[Passage] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    collection: str
    elapsed_ms: float
    error_type: str | None = None
    candidates: list[EntityCandidate] = Field(default_factory=list)
