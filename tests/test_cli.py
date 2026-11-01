import json
from unittest.mock import Mock

from nexusmind import cli


def test_failure_is_nonzero_and_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(cli, "execute", Mock(side_effect=RuntimeError("upstream down")))
    assert cli.main(["ingest"]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)["status"] == "failed"


def test_status_does_not_load_an_encoder(monkeypatch, tmp_path, capsys):
    from nexusmind.infrastructure.storage import Catalog

    catalog = Catalog(tmp_path / "catalog.sqlite")
    catalog.finish_run({"run_id": "test", "status": "completed", "patch": "16.1.1"})
    catalog.close()
    assert cli.main(["status", "--data-dir", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["run_id"] == "test"


def test_invalid_batch_size_fails_before_opening_runtime(tmp_path, capsys):
    path = tmp_path / "never-created"
    assert cli.main(["ingest", "--batch-size", "0", "--data-dir", str(path)]) == 1
    assert not path.exists()
    assert "batch-size" in capsys.readouterr().err


def test_retrieval_unavailable_has_nonzero_exit(monkeypatch, capsys):
    monkeypatch.setattr(cli, "execute", Mock(return_value={"status": "unavailable"}))
    assert cli.main(["retrieve", "Ahri", "--patch", "16.21.1"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "unavailable"


def test_coach_requires_free_tier_confirmation_before_opening_runtime(tmp_path, capsys):
    path = tmp_path / "never-created"
    assert cli.main(["coach", "Passif Ahri", "--patch", "16.21.1", "--data-dir", str(path)]) == 1
    assert not path.exists()
    assert "free-tier-confirmed" in capsys.readouterr().err


def test_coach_requires_key_before_loading_model(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert (
        cli.main(
            [
                "coach",
                "Passif Ahri",
                "--patch",
                "16.21.1",
                "--free-tier-confirmed",
                "--data-dir",
                str(tmp_path),
            ]
        )
        == 1
    )
    assert "GEMINI_API_KEY" in capsys.readouterr().err


def test_coach_quota_error_is_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(cli, "execute", Mock(return_value={"status": "quota_exceeded"}))
    assert cli.main(["coach", "Ahri", "--patch", "16.21.1"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "quota_exceeded"


def test_coach_cli_roundtrip_and_out_of_scope_without_external_services(
    monkeypatch, tmp_path, capsys
):
    from unittest.mock import MagicMock

    import qdrant_client
    import requests
    from test_coach import draft
    from test_documents import resource
    from test_ingestion import FakeEncoder

    from nexusmind.domain.documents import normalize
    from nexusmind.domain.evaluation import EvaluationSuite
    from nexusmind.infrastructure import embeddings
    from nexusmind.infrastructure.storage import Catalog
    from nexusmind.infrastructure.vector_store import VectorStore

    docs = normalize(resource())
    catalog = Catalog(tmp_path / "catalog.sqlite")
    catalog.save_documents(docs)
    catalog.close()
    encoder = FakeEncoder()
    client = qdrant_client.QdrantClient(":memory:")
    store = VectorStore(client, encoder)
    store.upsert(docs, encoder.encode([p.text for p in docs]))
    monkeypatch.setattr(embeddings, "SentenceEncoder", lambda *a, **kw: encoder)
    monkeypatch.setattr(qdrant_client, "QdrantClient", lambda **kw: client)
    # The composition root closes its client; reuse this in-memory fixture for two commands.
    monkeypatch.setattr(client, "close", Mock())
    transport = MagicMock()
    transport.__enter__.return_value = transport
    transport.post.return_value.status_code = 200
    transport.post.return_value.json.return_value = {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {
                            "text": draft(docs[1].id).model_dump_json(),
                        }
                    ]
                },
            }
        ],
    }
    monkeypatch.setattr(requests, "Session", lambda: transport)
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    options = ["--patch", "16.1.1", "--data-dir", str(tmp_path), "--free-tier-confirmed"]
    try:
        assert cli.main(["coach", "Décris le passif de Ahri", *options]) == 0
        result = json.loads(capsys.readouterr().out)
        assert result["status"] == "answered"
        assert result["sources"][0]["id"] == docs[1].id
        assert cli.main(["coach", "Comment freeze avec Ahri ?", *options]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == "out_of_scope"
        suite = EvaluationSuite(
            name="cli-plan",
            patch="16.1.1",
            locale="fr_FR",
            cases=[
                {
                    "id": "ahri",
                    "split": "validation",
                    "query": "Décris le passif de Ahri",
                    "expected_status": "ok",
                    "expected": [
                        {
                            "entity_type": "champion",
                            "entity_id": "Ahri",
                            "section": "passive",
                        }
                    ],
                }
            ],
        )
        questions = tmp_path / "suite.json"
        questions.write_text(suite.model_dump_json(), encoding="utf-8")
        report = tmp_path / "report.json"
        monkeypatch.delenv("GEMINI_API_KEY")
        assert (
            cli.main(
                [
                    "evaluate-coach",
                    "--suite",
                    str(questions),
                    "--output",
                    str(report),
                    "--data-dir",
                    str(tmp_path),
                ]
            )
            == 0
        )
        assert json.loads(capsys.readouterr().out)["status"] == "planned"
        assert json.loads(report.read_text(encoding="utf-8"))["calls_attempted"] == 0
        transport.post.assert_called_once()
    finally:
        type(client).close(client)


def test_coach_evaluation_live_requires_free_tier_before_loading_suite(capsys):
    assert (
        cli.main(["evaluate-coach", "--live", "--suite", "missing.json", "--output", "unused.json"])
        == 1
    )
    assert "free-tier-confirmed" in capsys.readouterr().err


def test_coach_can_read_key_from_hidden_interactive_prompt(monkeypatch, tmp_path, capsys):
    import getpass

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    prompt = Mock(return_value="private-key-from-terminal")
    monkeypatch.setattr(getpass, "getpass", prompt)
    assert (
        cli.main(
            [
                "coach",
                "Ahri",
                "--patch",
                "16.21.1",
                "--free-tier-confirmed",
                "--prompt-api-key",
                "--data-dir",
                str(tmp_path),
            ]
        )
        == 1
    )
    output = capsys.readouterr()
    assert "No catalog" in output.err
    assert "private-key-from-terminal" not in output.err + output.out
    assert "GEMINI_API_KEY" not in cli.os.environ
    prompt.assert_called_once()


def test_coach_and_evaluation_select_the_same_fast_default():
    coach = cli.parser().parse_args(["coach", "Ahri", "--patch", "16.21.1"])
    evaluation = cli.parser().parse_args(
        [
            "evaluate-coach",
            "--suite",
            "suite.json",
            "--output",
            "report.json",
        ]
    )
    assert coach.coach_model == evaluation.coach_model == "gemini-3.5-flash-lite"
    explicit = cli.parser().parse_args(
        [
            "coach",
            "Ahri",
            "--patch",
            "16.21.1",
            "--coach-model",
            "gemini-3.8-flash",
        ]
    )
    assert explicit.coach_model == "gemini-3.8-flash"


def test_serve_requires_free_tier_and_no_runtime_is_loaded(capsys):
    assert cli.main(["serve", "--patch", "16.21.1"]) == 1
    assert "free-tier-confirmed" in capsys.readouterr().err
