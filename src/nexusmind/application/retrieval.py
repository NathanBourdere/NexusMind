"""Conservative routing over a versioned catalogue, followed by filtered search."""

import re
import unicodedata
from collections.abc import Iterable
from time import perf_counter

from nexusmind.application.ports import SearchIndex
from nexusmind.domain.documents import Document
from nexusmind.domain.retrieval import Passage, RetrievalFilters, RetrievalRequest, RetrievalResult

# This finite scope gate is intentionally visible and testable, not a semantic oracle.
UNSUPPORTED = re.compile(
    r"\b(freeze|gel de vague|geler|wave|vagues?|macro|rotation|gank|winrate|taux de victoire|"
    r"build|combo optimal|meilleur|meilleure|strategie|matchup|derniere partie|mes parties|"
    r"ma partie|mon match|analyse|replay|classement|patch notes|note de patch|"
    r"notes de patch|frame data|frames|annuler une animation|comment jouer|quand acheter|"
    r"dois je|ou placer|comment gagner|contrer|roles?)\b"
)
LIMITS = [
    "Corpus Riot statique : ces passages ne constituent pas une réponse de coaching.",
    "Le score mesure la similarité, pas la probabilité de vérité.",
]


def folded(text: str) -> str:
    plain = "".join(
        char
        for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )
    return " ".join(re.sub(r"[^\w]+", " ", plain).split())


def contains(query: str, alias: str) -> bool:
    return bool(alias and re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", query))


def body(doc: Document) -> str:
    prefix = f"{doc.entity_id} / {doc.section.split(':chunk:')[0]}. "
    return doc.text.removeprefix(prefix)


def entity_aliases(docs: list[Document]) -> set[str]:
    aliases = {folded(docs[0].entity_id)} if not docs[0].entity_id.isdigit() else set()
    for doc in docs:
        if ":chunk:" in doc.section and not doc.section.endswith(":chunk:0"):
            continue
        text = body(doc)
        if doc.entity_type == "champion" and doc.section == "overview":
            aliases.add(folded(text.split(",", 1)[0]))
        elif doc.entity_type != "champion":
            aliases.add(folded(text.split(". ", 1)[0]))
    return {alias for alias in aliases if len(alias) >= 2}


def section_families(query: str, docs: list[Document]) -> set[str]:
    if docs[0].entity_type != "champion":
        return set()
    if re.search(r"\bpassifs?\b", query):
        return {"passive"}
    if re.search(r"\b(classes|classe|categories|categorie)\b", query):
        return {"overview"}
    named = set()
    for doc in docs:
        if " — " in body(doc):
            label = folded(body(doc).split(" — ", 1)[1].split(". ", 1)[0])
            if len(label) >= 3 and contains(query, label):
                named.add(doc.section.split(":chunk:")[0])
    if named:
        return named
    slots = re.findall(r"\b([qwer])\s+(?:de|d)\b", query)
    if re.search(r"\b(ultime|ulti|ultimate)\b", query):
        slots.append("r")
    exact = {
        doc.section.split(":chunk:")[0]
        for doc in docs
        if doc.section.startswith("spell:")
        and any(doc.section.split(":chunk:")[0].casefold().endswith(slot) for slot in slots)
    }
    if exact:
        return exact
    if re.search(r"\b(sorts?|competences?|capacites?)\b", query):
        return {doc.section.split(":chunk:")[0] for doc in docs if doc.section.startswith("spell:")}
    return set()


class Retriever:
    def __init__(self, store: SearchIndex, documents: Iterable[Document]):
        self.store = store
        self.documents = tuple(documents)

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        start = perf_counter()
        filters = RetrievalFilters(entity_type=request.entity_type, entity_ids=request.entity_ids)

        def result(status, reason=None, passages=None, error_type=None, candidates=None):
            return RetrievalResult(
                query=request.query,
                patch=request.patch,
                locale=request.locale,
                status=status,
                filters=filters,
                passages=passages or [],
                limitations=LIMITS + ([reason] if reason else []),
                collection=self.store.collection,
                elapsed_ms=round((perf_counter() - start) * 1000, 3),
                error_type=error_type,
                candidates=[
                    {"entity_type": kind, "entity_id": entity_id}
                    for kind, entity_id in (candidates or [])
                ],
            )

        query = folded(request.query)
        if UNSUPPORTED.search(query):
            return result(
                "out_of_scope", "Cette demande dépasse les descriptions statiques disponibles."
            )
        scoped = [
            doc
            for doc in self.documents
            if doc.patch == request.patch
            and doc.locale == request.locale
            and (request.entity_type is None or doc.entity_type == request.entity_type)
        ]
        if not scoped:
            return result("no_results", "Aucun document pour ce patch, cette langue et ce type.")
        grouped = {}
        for doc in scoped:
            grouped.setdefault((doc.entity_type, doc.entity_id), []).append(doc)
        found = [
            (alias, key)
            for key, docs in grouped.items()
            for alias in entity_aliases(docs)
            if contains(query, alias)
        ]
        if request.entity_ids:
            selected = [
                key
                for key in grouped
                if any(folded(key[1]) == folded(entity_id) for entity_id in request.entity_ids)
            ]
            if len(selected) != len(set(map(folded, request.entity_ids))):
                return result(
                    "no_results", "Au moins une entité explicite est absente du corpus filtré."
                )
            if found and not (set(selected) & {key for _, key in found}):
                return result(
                    "needs_clarification", "Les filtres explicites contredisent l'entité nommée."
                )
        else:
            if not found:
                return result(
                    "needs_clarification", "Préciser un champion, objet, rune ou sort d'invocateur."
                )
            # Remove aliases contained in a longer alias, but preserve distinct named entities.
            selected = sorted(
                {
                    key
                    for alias, key in found
                    if not any(alias != other and contains(other, alias) for other, _ in found)
                }
            )
            if len(selected) != 1:
                return result(
                    "needs_clarification",
                    "Plusieurs entités détectées : fournir des filtres explicites.",
                    candidates=selected,
                )
        kinds = {key[0] for key in selected}
        if len(kinds) != 1:
            return result("needs_clarification", "Préciser un seul type d'entité.")
        filters.entity_type = selected[0][0]
        filters.entity_ids = [key[1] for key in selected]
        chosen = [doc for key in selected for doc in grouped[key]]
        families = {request.section} if request.section else section_families(query, chosen)
        if families:
            filters.sections = sorted(
                {
                    doc.section
                    for doc in chosen
                    if any(
                        doc.section == family or doc.section.startswith(family + ":chunk:")
                        for family in families
                    )
                }
            )
            if not filters.sections:
                return result("no_results", "Section demandée absente du corpus filtré.")
        try:
            hits = self.store.search(
                request.query,
                patch=request.patch,
                locale=request.locale,
                limit=request.limit,
                entity_type=filters.entity_type,
                entity_ids=filters.entity_ids,
                sections=filters.sections or None,
            )
            passages = [
                Passage.model_validate({**hit["payload"], "score": hit["score"]}) for hit in hits
            ]
        except Exception as exc:
            return result(
                "unavailable",
                "La recherche a échoué ; aucune absence de connaissance n'est déduite.",
                error_type=type(exc).__name__,
            )
        return result("ok" if passages else "no_results", passages=passages)
