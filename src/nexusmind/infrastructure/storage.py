"""Durable normalized passages and run journal, independent of Qdrant volumes."""

import json
import sqlite3
from pathlib import Path

from nexusmind.domain.documents import Document


class Catalog:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, report TEXT NOT NULL
            );
        """)

    def close(self) -> None:
        self.connection.close()

    def start_run(self, run_id: str, metadata: dict) -> None:
        self.finish_run({"run_id": run_id, "status": "running", **metadata})

    def save_documents(self, documents: list[Document]) -> None:
        with self.connection:
            self.connection.executemany(
                "INSERT INTO documents(id, payload) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                [(doc.id, doc.model_dump_json()) for doc in documents],
            )

    def finish_run(self, report: dict) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO runs(run_id, report) VALUES (?, ?) "
                "ON CONFLICT(run_id) DO UPDATE SET report=excluded.report",
                (report["run_id"], json.dumps(report, ensure_ascii=False)),
            )

    def get_run(self, run_id: str) -> dict:
        row = self.connection.execute(
            "SELECT report FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row[0])

    def latest_run(self) -> dict:
        row = self.connection.execute(
            "SELECT report FROM runs ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No ingestion runs recorded")
        return json.loads(row[0])

    def document_count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    def documents(self) -> list[Document]:
        return [
            Document.model_validate_json(row[0])
            for row in self.connection.execute("SELECT payload FROM documents ORDER BY id")
        ]
