from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str
    source: str
    snippet: str


class AIChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000, description="User question or financial literacy prompt")
    language: str = Field(default="en", pattern="^(en|kn|hi)$")


class AIChatResponse(BaseModel):
    reply: str
    citations: list[Citation]
    pii_scrubbed: bool
    disclaimer: str = (
        "Educational financial literacy information only. FinSmart does not provide "
        "guaranteed stock, crypto, or speculative investment advice."
    )

