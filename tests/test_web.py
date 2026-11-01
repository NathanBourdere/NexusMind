from contextlib import contextmanager
from unittest.mock import Mock

from fastapi.testclient import TestClient

from nexusmind.domain.coaching import CoachResult
from nexusmind.web.app import create_app


def test_lifespan_reuses_one_runtime_and_closes_it():
    events = []
    runtime = Mock()
    runtime.answer.return_value = CoachResult(
        status="no_results", query="Ahri", patch="16.21.1", locale="fr_FR"
    )

    @contextmanager
    def factory():
        events.append("start")
        yield runtime
        events.append("stop")

    with TestClient(create_app(factory, patch="16.21.1"), base_url="http://127.0.0.1") as client:
        assert client.get("/health/ready").status_code == 200
        for _ in range(2):
            response = client.post("/api/chat", json={"query": "Ahri", "patch": "16.21.1"})
            assert response.status_code == 200
        assert events == ["start"]
        assert runtime.answer.call_count == 2
        assert "NexusMind" in client.get("/").text
    assert events == ["start", "stop"]


def test_invalid_request_and_foreign_origin_do_not_call_runtime():
    runtime = Mock()

    @contextmanager
    def factory():
        yield runtime

    with TestClient(create_app(factory, patch="16.21.1"), base_url="http://127.0.0.1") as client:
        assert client.post("/api/chat", json={"query": "", "patch": "16.21.1"}).status_code == 422
        assert (
            client.post(
                "/api/chat",
                json={"query": "Ahri", "patch": "16.21.1"},
                headers={"Origin": "https://elsewhere.example"},
            ).status_code
            == 403
        )
        runtime.answer.assert_not_called()
