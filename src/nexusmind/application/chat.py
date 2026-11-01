"""Reusable query pipeline and a process-local generation budget."""

from nexusmind.application.coach import Coach, Generator
from nexusmind.application.retrieval import Retriever
from nexusmind.domain.coaching import QuotaExceeded
from nexusmind.domain.postgame import PostGameReport
from nexusmind.domain.retrieval import RetrievalRequest


class BudgetedGenerator:
    def __init__(self, generator: Generator, max_calls: int = 30):
        if not 1 <= max_calls <= 100:
            raise ValueError("max-calls must be between 1 and 100")
        self.generator = generator
        self.model = generator.model
        self.max_calls = max_calls
        self.calls = 0

    def generate(self, evidence, level):
        if self.calls >= self.max_calls:
            raise QuotaExceeded("Process generation budget reached")
        self.calls += 1
        return self.generator.generate(evidence, level)


class ChatService:
    def __init__(self, retriever: Retriever, coach: Coach, analyst=None):
        self.retriever = retriever
        self.coach = coach
        self.analyst = analyst

    def answer(self, request: RetrievalRequest, level: str):
        return self.coach.respond(self.retriever.retrieve(request), level=level)

    def analyze(self, request):
        if self.analyst is None:
            return PostGameReport(
                status="unavailable",
                limitations=["La clé Riot n'est pas configurée sur le serveur."],
            )
        return self.analyst.analyze(request)
