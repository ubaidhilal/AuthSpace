import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agents import Runner, SQLiteSession
from app.core.config import settings
from app.db.session import get_db, SessionLocal
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatRequest, ConversationCreate
from app.services.agent_service import create_agent
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/conversations")
async def list_conversations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
    )
    rows = result.scalars().all()
    return {"conversations": [{"id": c.id, "title": c.title, "created_at": c.created_at, "updated_at": c.updated_at} for c in rows]}


@router.post("/conversations", status_code=201)
async def create_conversation(payload: ConversationCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation = Conversation(user_id=user.id, title=(payload.title or "New conversation").strip() or "New conversation")
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return {"id": conversation.id, "title": conversation.title, "created_at": conversation.created_at, "updated_at": conversation.updated_at}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation = await _owned_conversation(conversation_id, user.id, db)
    result = await db.execute(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at))
    messages = result.scalars().all()
    return {"id": conversation.id, 
            "title": conversation.title, 
            "messages": [{"id": m.id, "role": m.role,
            "content": m.content,
            "created_at": m.created_at} for m in messages]}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation = await _owned_conversation(conversation_id, user.id, db)
    await db.delete(conversation)
    await db.commit()
    return {"message" : "conversation deleted"}


async def _owned_conversation(conversation_id: str, user_id: str, db: AsyncSession) -> Conversation:
    try:
        UUID(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation ID") from exc
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

from app.services.agent_service import AssistantResponse
# generate(request, db, conversation_id, user.id, question)

async def generate(request, db, conversation_id, user_id, question):
    assistant_text = ""

    try:
        agent = await asyncio.to_thread(create_agent, user_id)

        memory = SQLiteSession(
            session_id=f"{user_id}:{conversation_id}"
        )

        run_result = Runner.run_streamed(
            agent,
            question,
            session=memory,
        )

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
            raise ValueError(
                "Agent did not return a structured AssistantResponse"
            )

        assistant_text = response_data["message"]
        connect_now = response_data.get("connect_now", False)
        connection = response_data.get("connection")

        # Save only the user-facing message, not the JSON structure.
        db.add(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_text,
            )
        )

        saved_conversation = await db.get(
            Conversation, conversation_id
        )

        if saved_conversation:
            saved_conversation.updated_at = datetime.now(timezone.utc)

        await db.commit()

        # Send the user-facing message to the frontend.
        yield sse(
            "token",
            {"delta": assistant_text},
        )

        # Send the complete structured response.
        yield sse(
            "done",
            {
                "conversation_id": str(conversation_id),
                "complete": assistant_text,
                "connect_now": connect_now,
                "connection": connection,
            },
        )

    except asyncio.CancelledError:
        raise

    except Exception:
        logger.exception(
            "Agent streaming failed for user=%s conversation=%s",
            user_id,
            conversation_id,
        )

        yield sse(
            "error",
            {
                "message": (
                    "The assistant could not complete this request. "
                    "Please try again."
                )
            },
        )



@router.post("/chat")
async def chat(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty",
        )

    if len(question) > settings.max_question_length:
        raise HTTPException(
            status_code=413,
            detail=f"Question exceeds {settings.max_question_length} characters",
        )

    if payload.conversation_id:
        conversation = await _owned_conversation(
            payload.conversation_id, user.id, db
        )
    else:
        conversation = Conversation(
            user_id=user.id,
            title=question[:60],
        )
        db.add(conversation)
        await db.flush()

    conversation_id = conversation.id
    conversation.title = (
        question[:60]
        if conversation.title == "New conversation"
        else conversation.title
    )

    db.add(
        Message(
            conversation_id=conversation_id,
            role="user",
            content=question,
        )
    )

    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # async def generate():
    #     COMPLETE = ""
    #     assistant_text = ""

    #     try:
    #         agent = await asyncio.to_thread(create_agent, user.id)

    #         memory = SQLiteSession(
    #             session_id=f"{user.id}:{conversation_id}"
    #         )

    #         result = Runner.run_streamed(
    #             agent,
    #             question,
    #             session=memory,
    #         )

    #         async for event in result.stream_events():
    #             if await request.is_disconnected():
    #                 logger.info(
    #                     "Client disconnected during stream; conversation=%s",
    #                     conversation_id,
    #                 )
    #                 break

    #             if (
    #                 event.type == "raw_response_event"
    #                 and getattr(event.data, "type", None)
    #                 == "response.output_text.delta"
    #             ):
    #                 delta = event.data.delta

    #                 assistant_text += delta
    #                 COMPLETE += delta

    #                 yield sse("token", {"delta": delta})

    #         # COMPLETE contains the entire response received so far.
    #         logger.info("Complete assistant response: %s", COMPLETE)

    #         # Use COMPLETE here for parsing or processing the full output.
    #         if assistant_text:
    #             db.add(
    #                 Message(
    #                     conversation_id=conversation_id,
    #                     role="assistant",
    #                     content=assistant_text,
    #                 )
    #             )

    #             result = await db.execute(
    #                 select(Conversation).where(
    #                     Conversation.id == conversation_id,
    #                     Conversation.user_id == user.id,
    #                 )
    #             )

    #             saved_conversation = result.scalar_one_or_none()

    #             if saved_conversation:
    #                 saved_conversation.updated_at = datetime.now(
    #                     timezone.utc
    #                 )

    #             await db.commit()

    #         yield sse(
    #             "done",
    #             {
    #                 "conversation_id": str(conversation_id),
    #                 "complete": COMPLETE,
    #             },
    #         )

    #     except asyncio.CancelledError:
    #         raise

    #     except Exception:
    #         logger.exception(
    #             "Agent streaming failed for user=%s conversation=%s",
    #             user.id,
    #             conversation_id,
    #         )

    #         yield sse(
    #             "error",
    #             {
    #                 "message": (
    #                     "The assistant could not complete this request. "
    #                     "Please try again."
    #                 )
    #             },
    #         )

    #         if assistant_text:
    #             try:
    #                 db.add(
    #                     Message(
    #                         conversation_id=conversation_id,
    #                         role="assistant",
    #                         content=assistant_text,
    #                     )
    #                 )
    #                 await db.commit()
    #             except Exception:
    #                 logger.exception(
    #                     "Could not save partial assistant response"
    #                 )

    return StreamingResponse(
        # generate(),
        generate(request, db, conversation_id, user.id, question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

