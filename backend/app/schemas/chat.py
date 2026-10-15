from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
