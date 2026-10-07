from fastapi import FastAPI
from pydantic import BaseModel, Field


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


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "enterprise-omnichannel-ai-assistant",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return ChatResponse(
        question=request.question,
        route="DEMO",
        answer=(
            "The API is running successfully. "
            "The enterprise AI assistant will be connected next."
        ),
        sources=[],
    )
