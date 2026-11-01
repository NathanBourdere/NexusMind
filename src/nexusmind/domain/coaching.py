"""Provider-independent coaching contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nexusmind.domain.retrieval import EntityCandidate, Passage


class QuotaExceeded(RuntimeError):
    pass


class InvalidGeneration(RuntimeError):
    pass


class ProviderUnavailable(RuntimeError):
    def __init__(self, *, status_code: int | None = None, reason: str = "http"):
        super().__init__("Generation provider unavailable")
        self.status_code = status_code
        self.reason = reason


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    kind: Literal["sourced_fact", "coaching_hypothesis"]
    text: str = Field(min_length=1, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1, max_length=5)


class CoachDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: Literal["answered", "insufficient_evidence"]
    claims: list[Claim] = Field(max_length=8)
    exercise: str = Field(max_length=1000)
    limitations: list[str] = Field(max_length=8)


class CoachResult(BaseModel):
    status: Literal[
        "answered",
        "insufficient_evidence",
        "needs_clarification",
        "out_of_scope",
        "no_results",
        "unavailable",
        "invalid_generation",
        "quota_exceeded",
    ]
    query: str
    patch: str
    locale: str
    claims: list[Claim] = Field(default_factory=list)
    exercise: str = ""
    sources: list[Passage] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    candidates: list[EntityCandidate] = Field(default_factory=list)
    model: str | None = None
    error_type: str | None = None
    provider_status: int | None = None
    provider_error: str | None = None
