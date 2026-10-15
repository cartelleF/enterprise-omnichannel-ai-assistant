import os
from functools import lru_cache
from typing import Protocol

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from src.api.rate_limit import enforce_rate_limit


app = FastAPI(
    title="Enterprise Omni-Channel AI Assistant",
    description=(
        "API for the Enterprise Omni-Channel AI Assistant "
        "portfolio demonstration."
    ),
    version="1.0.0",
)


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Question sent to the enterprise assistant.",
    )


class ChatResponse(BaseModel):
    question: str
    route: str
    answer: str
    sources: list[str]
    generation_mode: str | None = None


class AssistantServiceProtocol(Protocol):
    def ask(self, question: str) -> dict:
        ...


@lru_cache(maxsize=1)
def get_assistant_service() -> AssistantServiceProtocol:
    backend = os.getenv(
        "ASSISTANT_BACKEND", "local"
    ).strip().lower()

    if backend == "local":
        from src.api.local_demo_service import LocalDemoService
        return LocalDemoService()

    if backend == "local_ai":
        from src.api.local_ai_runtime import (
            build_local_ai_service_from_env,
        )
        return build_local_ai_service_from_env()

    if backend == "databricks":
        from src.api.runtime import build_demo_assistant_service_from_env

        return build_demo_assistant_service_from_env()

    raise ValueError(
        f"Unsupported ASSISTANT_BACKEND: {backend}"
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "enterprise-omnichannel-ai-assistant",
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(enforce_rate_limit)],
)
def chat(
    request: ChatRequest,
    service: AssistantServiceProtocol = Depends(
        get_assistant_service
    ),
):
    result = service.ask(request.question)

    return ChatResponse(
        question=request.question,
        route=result["route"],
        answer=result["answer"],
        sources=result.get("sources", []),
        generation_mode=result.get("generation_mode") or (
            "deterministic"
            if os.getenv("ASSISTANT_BACKEND", "local").strip().lower() == "local"
            else None
        ),
    )
