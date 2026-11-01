from unittest.mock import Mock

from test_coach import draft, evidence

from nexusmind.application.chat import BudgetedGenerator, ChatService
from nexusmind.application.coach import Coach
from nexusmind.domain.retrieval import RetrievalRequest


def test_chat_reuses_dependencies_and_budget_blocks_extra_generation():
    found = evidence()
    provider = Mock(model="test", generate=Mock(return_value=draft(found.passages[0].id)))
    budget = BudgetedGenerator(provider, max_calls=1)
    retriever = Mock(retrieve=Mock(return_value=found))
    service = ChatService(retriever, Coach(budget))
    request = RetrievalRequest(query="Ahri", patch="16.1.1")
    assert service.answer(request, "beginner").status == "answered"
    assert service.answer(request, "beginner").status == "quota_exceeded"
    assert budget.calls == 1
    provider.generate.assert_called_once()


def test_abstention_does_not_consume_server_budget():
    provider = Mock(model="test")
    budget = BudgetedGenerator(provider, max_calls=1)
    retriever = Mock(retrieve=Mock(return_value=evidence("out_of_scope")))
    service = ChatService(retriever, Coach(budget))
    assert (
        service.answer(RetrievalRequest(query="macro", patch="16.1.1"), "beginner").status
        == "out_of_scope"
    )
    assert budget.calls == 0
    provider.generate.assert_not_called()
