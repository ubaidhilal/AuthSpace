import asyncio
import json
import logging

from uuid import UUID
from datetime import datetime, timezone
from app.services.agent_service import create_agent,AssistantResponse
from fastapi import HTTPException
from agents import Runner, SQLiteSession
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation,Message
from sqlalchemy import select


logger = logging.getLogger(__name__)


def sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

async def owned_conversation(conversation_id: str, user_id: str, db: AsyncSession) -> Conversation:
    try:
        UUID(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation ID") from exc
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation



async def generate(request, db, conversation_id, user_id, question):
    assistant_text = ""
    try:
        agent = await asyncio.to_thread(create_agent, user_id)
        memory = SQLiteSession(session_id=f"{user_id}:{conversation_id}")
        run_result = Runner.run_streamed(agent,question,session=memory,)
        # Consume the stream until the structured output is ready.
        async for event in run_result.stream_events():
            if await request.is_disconnected():
                logger.info(
                    "Client disconnected during stream; conversation=%s",
                    conversation_id,
                )
                return
        # Extract the final structured Pydantic response.
        structured = run_result.final_output
        if isinstance(structured, AssistantResponse):
            response_data = structured.model_dump(mode="json")
        elif isinstance(structured, dict):
            response_data = structured
        else:
            raise ValueError("Agent did not return a structured AssistantResponse")

        assistant_text = response_data["message"]
        connect_now = response_data.get("connect_now", False)
        connection = response_data.get("connection")

        # Save only the user-facing message, not the JSON structure.
        db.add(
            Message(conversation_id=conversation_id,
                role="assistant",
                content=assistant_text))
        saved_conversation = await db.get(Conversation, conversation_id)
        if saved_conversation:
            saved_conversation.updated_at = datetime.now(timezone.utc)

        await db.commit()

        # Send the user-facing message to the frontend.
        yield sse("token",{"delta": assistant_text})

        # Send the complete structured response.
        yield sse("done",
                   {
                   "conversation_id": str(conversation_id),
                   "complete": assistant_text,
                   "connect_now": connect_now,
                   "connection": connection,
                   })
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "Agent streaming failed for user=%s conversation=%s",
            user_id,
            conversation_id,
        )

        yield sse("error",
                  {
                  "message": (
                   "The assistant could not complete this request. "
                   "Please try again."
                  )
              })

