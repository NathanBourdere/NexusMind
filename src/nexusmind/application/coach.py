"""Bounded generation with citation membership checks, without a second LLM."""

from typing import Protocol

from nexusmind.domain.coaching import (
    CoachDraft,
    CoachResult,
    InvalidGeneration,
    ProviderUnavailable,
    QuotaExceeded,
)
from nexusmind.domain.retrieval import RetrievalResult


class Generator(Protocol):
    model: str

    def generate(self, evidence: RetrievalResult, level: str) -> CoachDraft: ...


class Coach:
    def __init__(self, generator: Generator):
        self.generator = generator

    def respond(self, evidence: RetrievalResult, *, level: str = "beginner") -> CoachResult:
        result = CoachResult(
            status="insufficient_evidence",
            query=evidence.query,
            patch=evidence.patch,
            locale=evidence.locale,
            limitations=list(evidence.limitations),
            candidates=evidence.candidates,
        )
        if level not in {"beginner", "intermediate", "advanced"}:
            raise ValueError("Unknown coaching level")
        if evidence.status != "ok":
            return result.model_copy(
                update={"status": evidence.status, "error_type": evidence.error_type}
            )
        if not evidence.passages:
            return result
        # No silent truncation or cross-version evidence. Single generation, no retries.
        if (
            len(evidence.passages) > 5
            or sum(len(p.text) for p in evidence.passages) > 8000
            or any(
                p.patch != evidence.patch or p.locale != evidence.locale for p in evidence.passages
            )
        ):
            return result.model_copy(
                update={"status": "invalid_generation", "error_type": "InvalidEvidence"}
            )
        result.model = self.generator.model
        try:
            draft = self.generator.generate(evidence, level)
            if draft.status == "insufficient_evidence":
                result.limitations += draft.limitations
                return result
            allowed = {p.id for p in evidence.passages}
            cited = {ref for claim in draft.claims for ref in claim.evidence_ids}
            if not draft.claims or not cited <= allowed:
                return result.model_copy(
                    update={"status": "invalid_generation", "error_type": "InvalidCitations"}
                )
            result.status = "answered"
            result.claims = draft.claims
            result.exercise = draft.exercise
            result.sources = [p for p in evidence.passages if p.id in cited]
            result.limitations += draft.limitations
            result.limitations.append(
                "Les références sont vérifiées ; leur soutien sémantique aux affirmations "
                "nécessite une évaluation. Les conseils restent des hypothèses de coaching."
            )
            return result
        except ProviderUnavailable as exc:
            return result.model_copy(
                update={
                    "status": "unavailable",
                    "error_type": type(exc).__name__,
                    "provider_status": exc.status_code,
                    "provider_error": exc.reason,
                }
            )
        except (InvalidGeneration, QuotaExceeded) as exc:
            return result.model_copy(
                update={
                    "status": "quota_exceeded"
                    if isinstance(exc, QuotaExceeded)
                    else "invalid_generation",
                    "error_type": type(exc).__name__,
                }
            )
        except Exception as exc:
            # Never expose provider payloads, request URLs, API keys or exception messages.
            return result.model_copy(
                update={"status": "unavailable", "error_type": type(exc).__name__}
            )
