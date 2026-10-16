from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.conversation import Conversation
from app.repositories import repos
from app.utils.helpers import generate


async def list_conversations_service(db: AsyncSession,user_id: str) ->list[Conversation]:
    return await repos.list_user_conversations(db, user_id)

async def create_conversation_service(db: AsyncSession,user_id: str,title: str | None)-> Conversation:
    return await repos.create_conversation(
        db=db,
        user_id=user_id,
        title=title or "New conversation")

async def get_conversation_service(db: AsyncSession,conversation_id: str,user_id: str)-> tuple[Conversation, list]:
    conversation = await repos.get_owned_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id)
    messages = await repos.get_conversation_messages(
        db=db,
        conversation_id=conversation.id)
    return conversation, messages


async def delete_conversation_service(db: AsyncSession,conversation_id: str,user_id: str):
    conversation = await repos.get_owned_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id)
    await repos.delete_conversation(db, conversation)
    
    
    
async def chat_service(request: Request,db: AsyncSession,user_id: str, question: str,    conversation_id: str | None):
    question = question.strip()
    if not question:
        raise HTTPException(status_code=422,detail="Question cannot be empty")
    if len(question) > settings.max_question_length:
        raise HTTPException(status_code=413,detail=(f"Question exceeds"f"{settings.max_question_length} characters"))                                           
    if conversation_id:
        conversation = await repos.get_owned_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )
    else:
        conversation = Conversation(user_id=user_id,title=question[:60])
        db.add(conversation)
        await db.flush()
    await repos.save_user_message(db=db,conversation=conversation,question=question)
    return generate(request,db,conversation.id, user_id, question)
