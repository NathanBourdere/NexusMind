"""Local interface with an injected lifespan; never constructs ML at import."""

from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from nexusmind.domain.retrieval import RetrievalRequest


class ChatRequest(RetrievalRequest):
    limit: int = Field(default=5, ge=1, le=5)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"


def create_app(runtime_factory, *, patch: str, locale: str = "fr_FR"):
    RetrievalRequest(query="startup", patch=patch, locale=locale)
    gate = Lock()

    @asynccontextmanager
    async def lifespan(app):
        with runtime_factory() as runtime:
            app.state.runtime = runtime
            yield
        app.state.runtime = None

    app = FastAPI(title="NexusMind", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin != f"{request.url.scheme}://{request.headers.get('host', '')}":
            return JSONResponse({"status": "forbidden"}, status_code=403)
        if request.method == "POST" and len(await request.body()) > 16384:
            return JSONResponse({"status": "request_too_large"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return JSONResponse({"status": "invalid_request"}, status_code=422)

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready():
        return {"status": "ready"}

    @app.get("/api/config")
    def config():
        return {"patch": patch, "locale": locale}

    @app.post("/api/chat")
    def chat(payload: ChatRequest):
        if not gate.acquire(blocking=False):
            raise HTTPException(429, "Une réponse est déjà en cours.")
        try:
            request = RetrievalRequest(**payload.model_dump(exclude={"level"}))
            result = app.state.runtime.answer(request, payload.level)
            code = {"quota_exceeded": 429, "unavailable": 503, "invalid_generation": 502}.get(
                result.status, 200
            )
            return JSONResponse(result.model_dump(), status_code=code)
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        finally:
            gate.release()

    assets = Path(__file__).parent / "assets"
    app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    def index():
        return FileResponse(assets / "index.html")

    return app
