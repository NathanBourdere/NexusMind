"""Own one encoder, index and HTTP session for the server lifespan."""

import os
from contextlib import ExitStack, contextmanager

import requests
from qdrant_client import QdrantClient

from nexusmind.application.chat import BudgetedGenerator, ChatService
from nexusmind.application.coach import Coach
from nexusmind.application.postgame import PostGameAnalyst
from nexusmind.application.retrieval import Retriever
from nexusmind.infrastructure.embeddings import SentenceEncoder
from nexusmind.infrastructure.gemini import GeminiGenerator
from nexusmind.infrastructure.riot_live import RiotMatchSource
from nexusmind.infrastructure.storage import Catalog
from nexusmind.infrastructure.vector_store import VectorStore


@contextmanager
def open_runtime(args, api_key):
    if not (args.data_dir / "catalog.sqlite").exists():
        raise ValueError("No catalog; run ingestion first")
    with ExitStack() as stack:
        encoder = SentenceEncoder(
            args.model, args.revision, offline=args.offline_model, cache_folder=args.model_cache
        )
        client = (
            QdrantClient(url=args.qdrant_url, timeout=30)
            if args.qdrant_url
            else QdrantClient(
                path=str(args.data_dir / "qdrant"), force_disable_check_same_thread=True
            )
        )
        stack.callback(client.close)
        catalog = Catalog(args.data_dir / "catalog.sqlite")
        try:
            documents = catalog.documents()
        finally:
            catalog.close()
        session = stack.enter_context(requests.Session())
        generator = BudgetedGenerator(
            GeminiGenerator(api_key, session=session, model=args.coach_model), args.max_calls
        )
        store = VectorStore(client, encoder, create_indexes=bool(args.qdrant_url))
        riot_key = os.environ.get("RIOT_API_KEY", "").strip()
        analyst = PostGameAnalyst(RiotMatchSource(riot_key, session=session)) if riot_key else None
        yield ChatService(Retriever(store, documents), Coach(generator), analyst)
