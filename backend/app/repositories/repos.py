from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message


async def list_user_conversations(db: AsyncSession, user_id: str) ->list[Conversation]:
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user_id).order_by(
            Conversation.updated_at.desc()))
    return list(result.scalars().all())

async def get_owned_conversation(db: AsyncSession,conversation_id: str,user_id: str)-> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404,detail="Conversation not found")
    return conversation


async def get_conversation_messages(db: AsyncSession,conversation_id: str) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at))
    return list(result.scalars().all())

async def create_conversation(db: AsyncSession,user_id: str,title: str) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        title=title.strip() or "New conversation")
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation

async def save_user_message(db: AsyncSession,conversation: Conversation,question: str) -> None:
    db.add(Message(
            conversation_id=conversation.id,
            role="user",
            content=question))
    if conversation.title == "New conversation":
        conversation.title = question[:60]
    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    
async def delete_conversation(db: AsyncSession,conversation: Conversation)-> None:
    await db.delete(conversation)
    await db.commit()    