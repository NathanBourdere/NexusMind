"""Composition root: construct infrastructure only for the selected command."""

import argparse
import json
import os
import sys
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

from nexusmind.infrastructure.embeddings import DEFAULT_MODEL, DEFAULT_REVISION


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
    search = commands.add_parser("search", parents=[common], help="Verify indexed passages")
    search.add_argument("query")
    search.add_argument("--patch", required=True)
    search.add_argument("--locale", default="fr_FR")
    search.add_argument("--limit", type=int, default=5)
    status = commands.add_parser("status", help="Read the last ingestion report without loading ML")
    status.add_argument("--data-dir", type=Path, default=Path(".runtime"))
    return root


def execute(args: argparse.Namespace) -> dict | list:
    from nexusmind.infrastructure.storage import Catalog

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
            return store.search(args.query, patch=args.patch, locale=args.locale, limit=args.limit)
        catalog = Catalog(args.data_dir / "catalog.sqlite")
        stack.callback(catalog.close)
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
    return 0
