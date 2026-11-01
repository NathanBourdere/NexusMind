"""Composition root: construct infrastructure only for the selected command."""

import argparse
import json
import os
import sys
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

from nexusmind.domain.postgame import REGIONS
from nexusmind.infrastructure.embeddings import DEFAULT_MODEL, DEFAULT_REVISION
from nexusmind.infrastructure.gemini import COACH_MODELS, DEFAULT_COACH_MODEL


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="nexusmind")
    commands = root.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", type=Path, default=Path(".runtime"))
    common.add_argument("--qdrant-url", default=os.environ.get("NEXUSMIND_QDRANT_URL"))
    common.add_argument("--model", default=DEFAULT_MODEL)
    common.add_argument("--revision", default=DEFAULT_REVISION)
    common.add_argument("--offline-model", action="store_true")
    common.add_argument("--model-cache")
    ingest = commands.add_parser("ingest", parents=[common], help="Ingest official Riot knowledge")
    ingest.add_argument("--patch", help="Data Dragon version; default: resolve once from Riot")
    ingest.add_argument("--locale", default="fr_FR")
    ingest.add_argument("--champion", action="append", dest="champions")
    ingest.add_argument(
        "--kind", action="append", choices=["champion", "item", "rune", "summoner_spell"]
    )
    ingest.add_argument("--batch-size", type=int, default=32)
    collect = commands.add_parser("collect-knowledge", help="Collect approved public references")
    collect.add_argument("--source", action="append", choices=["riot-guide", "communitydragon"])
    collect.add_argument("--patch", help="Pinned CommunityDragon major.minor patch")
    collect.add_argument("--locale", choices=["fr_FR", "en_US"], default="fr_FR")
    collect.add_argument("--champion-id", type=int, action="append", dest="champion_ids")
    collect.add_argument("--output", type=Path, required=True)
    knowledge = commands.add_parser(
        "ingest-knowledge",
        parents=[common],
        help="Index attributed source articles from a local JSON file",
    )
    knowledge.add_argument("--input", type=Path, required=True)
    knowledge.add_argument("--batch-size", type=int, default=32)
    search = commands.add_parser("search", parents=[common], help="Verify indexed passages")
    search.add_argument("query")
    search.add_argument("--patch", required=True)
    search.add_argument("--locale", default="fr_FR")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--entity-type", choices=["champion", "item", "rune", "summoner_spell"])
    search.add_argument("--entity-id", action="append", dest="entity_ids")
    search.add_argument("--section", action="append", dest="sections")
    retrieve = commands.add_parser(
        "retrieve", parents=[common], help="Retrieve structured evidence or abstain"
    )
    retrieve.add_argument("query")
    retrieve.add_argument("--patch", required=True)
    retrieve.add_argument("--locale", default="fr_FR")
    retrieve.add_argument("--limit", type=int, default=5)
    retrieve.add_argument("--entity-type", choices=["champion", "item", "rune", "summoner_spell"])
    retrieve.add_argument("--entity-id", action="append", dest="entity_ids")
    retrieve.add_argument("--section")
    retrieve.add_argument("--corpus", choices=["auto", "static", "reference"], default="auto")
    coach = commands.add_parser("coach", parents=[common], help="Explain retrieved Riot evidence")
    coach.add_argument("query")
    coach.add_argument("--patch", required=True)
    coach.add_argument("--locale", default="fr_FR")
    coach.add_argument("--limit", type=int, default=5)
    coach.add_argument("--entity-type", choices=["champion", "item", "rune", "summoner_spell"])
    coach.add_argument("--entity-id", action="append", dest="entity_ids")
    coach.add_argument("--section")
    coach.add_argument("--corpus", choices=["auto", "static", "reference"], default="auto")
    coach.add_argument(
        "--level", choices=["beginner", "intermediate", "advanced"], default="beginner"
    )
    coach.add_argument(
        "--free-tier-confirmed",
        action="store_true",
        help="Confirm this key belongs to a project without billing enabled",
    )
    coach.add_argument("--prompt-api-key", action="store_true", help="Read a key without echo")
    coach.add_argument("--coach-model", choices=COACH_MODELS, default=DEFAULT_COACH_MODEL)
    evaluation = commands.add_parser(
        "evaluate", parents=[common], help="Compare retrieval on an annotated suite"
    )
    evaluation.add_argument("--suite", type=Path, required=True)
    evaluation.add_argument("--output", type=Path, required=True)
    coach_evaluation = commands.add_parser(
        "evaluate-coach", parents=[common], help="Plan or run a bounded Coach evaluation"
    )
    coach_evaluation.add_argument("--suite", type=Path, required=True)
    coach_evaluation.add_argument("--output", type=Path, required=True)
    coach_evaluation.add_argument("--live", action="store_true")
    coach_evaluation.add_argument("--free-tier-confirmed", action="store_true")
    coach_evaluation.add_argument("--prompt-api-key", action="store_true")
    coach_evaluation.add_argument(
        "--coach-model", choices=COACH_MODELS, default=DEFAULT_COACH_MODEL
    )
    coach_evaluation.add_argument("--max-calls", type=int, default=3)
    coach_evaluation.add_argument("--call-interval", type=float, default=5)
    coach_evaluation.add_argument(
        "--level", choices=["beginner", "intermediate", "advanced"], default="beginner"
    )
    status = commands.add_parser("status", help="Read the last ingestion report without loading ML")
    status.add_argument("--data-dir", type=Path, default=Path(".runtime"))
    serve = commands.add_parser(
        "serve", parents=[common], help="Start the local coaching interface"
    )
    serve.add_argument("--patch", required=True)
    serve.add_argument("--locale", default="fr_FR")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--free-tier-confirmed", action="store_true")
    serve.add_argument("--prompt-api-key", action="store_true")
    serve.add_argument("--coach-model", choices=COACH_MODELS, default=DEFAULT_COACH_MODEL)
    serve.add_argument("--max-calls", type=int, default=30)
    postgame = commands.add_parser("analyze-match", help="Analyze one completed Riot match")
    postgame.add_argument("riot_id")
    postgame.add_argument("--region", choices=REGIONS, default="EUW")
    postgame.add_argument("--match-id")
    postgame.add_argument("--output", type=Path)
    return root


def execute(args: argparse.Namespace) -> dict | list:
    from nexusmind.infrastructure.storage import Catalog

    articles = None
    if args.command == "collect-knowledge":
        from nexusmind.infrastructure.knowledge_sources import (
            CommunityDragonSource,
            RiotGuideSource,
        )

        if args.output.exists():
            raise ValueError("Collection output already exists; choose a new path")
        sources = list(dict.fromkeys(args.source or ["riot-guide"]))
        if "communitydragon" in sources and (not args.patch or not args.champion_ids):
            raise ValueError("CommunityDragon requires --patch major.minor and --champion-id")
        if "riot-guide" in sources and args.locale != "fr_FR":
            raise ValueError("The Riot guide connector currently supports fr_FR only")
        articles = []
        with ExitStack() as stack:
            for name in sources:
                source = CommunityDragonSource() if name == "communitydragon" else RiotGuideSource()
                stack.callback(source.close)
                articles.extend(
                    source.collect(
                        patch=args.patch, locale=args.locale, champions=args.champion_ids
                    )
                    if name == "communitydragon"
                    else source.collect()
                )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump([a.model_dump() for a in articles], output, ensure_ascii=False, indent=2)
        return {
            "status": "completed",
            "articles": len(articles),
            "sources": sources,
            "output": str(args.output),
        }
    if args.command == "ingest-knowledge":
        from nexusmind.infrastructure.knowledge_sources import import_articles

        if args.batch_size < 1:
            raise ValueError("batch-size must be positive")
        articles = import_articles(args.input)

    if args.command == "analyze-match":
        from nexusmind.application.postgame import PostGameAnalyst
        from nexusmind.domain.postgame import PostGameRequest
        from nexusmind.infrastructure.riot_live import RiotMatchSource

        request = PostGameRequest(riot_id=args.riot_id, region=args.region, match_id=args.match_id)
        key = os.environ.get("RIOT_API_KEY", "").strip()
        if not key:
            raise ValueError("RIOT_API_KEY is required")
        if args.output and args.output.exists():
            raise ValueError("Analysis output already exists; choose a new path")
        source = RiotMatchSource(key)
        try:
            result = PostGameAnalyst(source).analyze(request).model_dump()
        finally:
            source.close()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as output:
                json.dump(result, output, ensure_ascii=False, indent=2)
        return result

    suite = None
    request = None
    api_key = None
    if args.command in {"coach", "serve"} or (args.command == "evaluate-coach" and args.live):
        if not args.free_tier_confirmed:
            raise ValueError("Use --free-tier-confirmed only for a project without billing enabled")
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key and args.prompt_api_key:
            import getpass

            if not sys.stdin.isatty():
                raise ValueError("--prompt-api-key requires an interactive terminal")
            api_key = getpass.getpass("Clé Gemini (saisie masquée, non enregistrée) : ").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required; never put it in a command argument")
        if args.command == "coach" and not 1 <= args.limit <= 5:
            raise ValueError("Coach limit must be between 1 and 5")
    if args.command == "serve":
        if not 1 <= args.port <= 65535 or not 1 <= args.max_calls <= 100:
            raise ValueError("Invalid port or generation budget")
        try:
            import uvicorn

            from nexusmind.web.app import create_app
            from nexusmind.web.runtime import open_runtime
        except ImportError:
            raise ValueError("Install the web extra: uv sync --extra web") from None
        app = create_app(lambda: open_runtime(args, api_key), patch=args.patch, locale=args.locale)
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
        return {"status": "stopped_normally"}
    if args.command in {"retrieve", "coach"}:
        from nexusmind.domain.retrieval import RetrievalRequest

        request = RetrievalRequest(
            query=args.query,
            patch=args.patch,
            locale=args.locale,
            limit=args.limit,
            entity_type=args.entity_type,
            entity_ids=args.entity_ids or [],
            section=args.section,
            corpus=args.corpus,
        )
    if args.command in {"evaluate", "evaluate-coach"}:
        from nexusmind.domain.evaluation import EvaluationSuite

        suite = EvaluationSuite.model_validate_json(args.suite.read_text(encoding="utf-8"))
        if args.output.resolve() == args.suite.resolve():
            raise ValueError("Evaluation output cannot overwrite its question suite")
        if args.command == "evaluate-coach":
            if not 1 <= args.max_calls <= 30:
                raise ValueError("max-calls must be between 1 and 30")
            if args.output.exists():
                raise ValueError("Coach report already exists; choose a new output path")
    if (
        args.command in {"retrieve", "coach", "evaluate", "evaluate-coach"}
        and not (args.data_dir / "catalog.sqlite").exists()
    ):
        raise ValueError("No catalog; run ingestion first")

    if args.command == "status":
        path = args.data_dir / "catalog.sqlite"
        if not path.exists():
            raise ValueError("No catalog; run ingestion first")
        catalog = Catalog(path)
        try:
            return catalog.latest_run()
        finally:
            catalog.close()

    from qdrant_client import QdrantClient

    from nexusmind.application.scout import ScoutAgent
    from nexusmind.infrastructure.embeddings import SentenceEncoder
    from nexusmind.infrastructure.riot import KINDS, RiotSource
    from nexusmind.infrastructure.vector_store import VectorStore

    if args.command == "search" and args.limit < 1:
        raise ValueError("limit must be positive")
    if args.command == "ingest" and args.batch_size < 1:
        raise ValueError("batch-size must be positive")
    if args.command == "ingest" and args.champions and args.kind and "champion" not in args.kind:
        raise ValueError("--champion requires --kind champion or the default kinds")

    with ExitStack() as stack:
        encoder = SentenceEncoder(
            args.model, args.revision, offline=args.offline_model, cache_folder=args.model_cache
        )
        args.data_dir.mkdir(parents=True, exist_ok=True)
        if args.qdrant_url:
            client = QdrantClient(url=args.qdrant_url, timeout=30)
        else:
            client = QdrantClient(path=str(args.data_dir / "qdrant"))
        stack.callback(client.close)
        store = VectorStore(client, encoder, create_indexes=bool(args.qdrant_url))
        if args.command == "search":
            return store.search(
                args.query,
                patch=args.patch,
                locale=args.locale,
                limit=args.limit,
                entity_type=args.entity_type,
                entity_ids=args.entity_ids,
                sections=args.sections,
            )
        catalog = Catalog(args.data_dir / "catalog.sqlite")
        stack.callback(catalog.close)
        if args.command == "ingest-knowledge":
            scout = ScoutAgent(
                None, encoder, store, catalog, args.data_dir / "raw", args.batch_size
            )
            return asdict(scout.ingest_articles(articles))
        if args.command == "retrieve":
            from nexusmind.application.retrieval import Retriever

            return Retriever(store, catalog.documents()).retrieve(request).model_dump()
        if args.command == "coach":
            import requests

            from nexusmind.application.coach import Coach
            from nexusmind.application.retrieval import Retriever
            from nexusmind.infrastructure.gemini import GeminiGenerator

            evidence = Retriever(store, catalog.documents()).retrieve(request)
            with requests.Session() as session:
                generator = GeminiGenerator(api_key, session=session, model=args.coach_model)
                return Coach(generator).respond(evidence, level=args.level).model_dump()
        if args.command == "evaluate-coach":
            import requests

            from nexusmind.application.coach_evaluation import evaluate_coach
            from nexusmind.application.retrieval import Retriever
            from nexusmind.infrastructure.gemini import GeminiGenerator

            with requests.Session() as session:
                generator = (
                    GeminiGenerator(api_key, session=session, model=args.coach_model)
                    if args.live
                    else None
                )
                documents = catalog.documents()
                report = evaluate_coach(
                    suite,
                    Retriever(store, documents),
                    documents,
                    generator,
                    max_calls=args.max_calls,
                    level=args.level,
                    call_interval=args.call_interval,
                )
            report["embedding"] = {"name": encoder.model_name, "revision": encoder.revision}
            report["collection"] = store.collection
            # Exclusive creation preserves existing reports, suites and corpus files.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as output:
                json.dump(report, output, ensure_ascii=False, indent=2)
            return {
                key: report[key]
                for key in ("status", "stop_reason", "calls_attempted", "max_calls")
            } | {
                "report_path": str(args.output),
                "cases": len(report["cases"]),
            }
        if args.command == "evaluate":
            from importlib.metadata import version

            from nexusmind.application.evaluation import evaluate

            report = evaluate(
                suite,
                store,
                catalog.documents(),
                {
                    "name": encoder.model_name,
                    "revision": encoder.revision,
                    "dimension": encoder.dimension,
                    "runtime_versions": {
                        name: version(name)
                        for name in ("qdrant-client", "sentence-transformers", "torch", "pydantic")
                    },
                    "python": sys.version.split()[0],
                },
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_suffix(".tmp")
            temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(args.output)
            return {
                "report_path": str(args.output),
                "suite": report["suite"],
                "corpus": report["corpus"],
                "summaries": report["summaries"],
            }
        source = RiotSource()
        stack.callback(source.close)
        scout = ScoutAgent(source, encoder, store, catalog, args.data_dir / "raw", args.batch_size)
        return asdict(
            scout.ingest(
                locale=args.locale,
                kinds=args.kind or list(KINDS),
                patch=args.patch,
                champions=args.champions,
            )
        )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = execute(args)
    except Exception as exc:
        print(
            json.dumps(
                {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if isinstance(result, dict) and result.get("status") in {
        "unavailable",
        "invalid_generation",
        "quota_exceeded",
        "stopped",
        "authentication_failed",
        "rate_limited",
    }:
        return 1
    return 0
