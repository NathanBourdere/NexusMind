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
