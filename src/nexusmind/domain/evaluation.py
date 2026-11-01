from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nexusmind.domain.retrieval import EntityType, RetrievalRequest


class GoldSelector(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: EntityType
    entity_id: str
    section: str


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    split: Literal["development", "validation"]
    query: str
    expected_status: Literal["ok", "no_results", "out_of_scope", "needs_clarification"]
    expected: list[GoldSelector] = Field(default_factory=list)
    patch: str | None = None
    locale: str | None = None
    entity_type: EntityType | None = None
    entity_ids: list[str] = Field(default_factory=list)
    rationale: str | None = None

    @model_validator(mode="after")
    def validate_gold(self):
        if bool(self.expected) != (self.expected_status == "ok"):
            raise ValueError("Positive cases require gold; negative cases cannot contain it")
        return self


class EvaluationSuite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    patch: str
    locale: str
    cases: list[EvaluationCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_cases(self):
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Evaluation case IDs must be unique")
        for case in self.cases:
            self.request_for(case)
        return self

    def request_for(self, case: EvaluationCase) -> RetrievalRequest:
        return RetrievalRequest(
            query=case.query,
            patch=case.patch or self.patch,
            locale=case.locale or self.locale,
            limit=5,
            entity_type=case.entity_type,
            entity_ids=case.entity_ids,
        )
