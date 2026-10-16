import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ConversationCreate
from app.services import services

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.get("/conversations")
async def list_conversations(user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    conversations = await services.list_conversations_service(db=db,user_id=user.id)
    return {
        "conversations": [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            }
            for conversation in conversations
        ]
    }
    
    
@router.post("/conversations", status_code=201)
async def create_conversation(payload: ConversationCreate,user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation = await services.create_conversation_service(db=db, user_id=user.id,title=payload.title)
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }    
    
    
    
@router.get("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation, messages = await services.get_conversation_service(
        db=db,
        conversation_id=conversation_id,
        user_id=user.id)
    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }
    

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await services.delete_conversation_service(
        db=db,
        conversation_id=conversation_id,
        user_id=user.id)
    return {"message": "conversation deleted"}    



@router.post("/chat")
async def chat(payload: ChatRequest,request: Request,user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stream = await services.chat_service(
        request=request,
        db=db,
        user_id=user.id,
        question=payload.question,
        conversation_id=payload.conversation_id)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        })
    
    
    
    