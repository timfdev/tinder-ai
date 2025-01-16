from fastapi import APIRouter
from shared.models import (
    MessageResponse,
    ReplyRequest,
    OpeningMessageRequest,
)
from messenger.app.dependencies import DatingAgentDep
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate/opener")
async def generate_opener(
    request: OpeningMessageRequest,
    agent: DatingAgentDep
) -> MessageResponse:
    """Generate opening message based on profile"""
    try:
        response = await agent.handle_message(
            match_id=request.profile.match_id,
            profile=request.profile.model_dump(),
            message=None  # None indicates we want an opener
        )
        return MessageResponse(message=response)
    except Exception as e:
        logger.error(f"Error generating opener: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/reply")
async def generate_reply(
    request: ReplyRequest,
    agent: DatingAgentDep
) -> MessageResponse:
    """Generate reply based on profile and conversation history"""
    try:
        response = await agent.handle_message(
            match_id=request.profile.match_id,
            profile=request.profile.model_dump(),
            message=request.last_messages[-1] if request.last_messages else None
        )
        return MessageResponse(message=response)
    except Exception as e:
        logger.error(f"Error generating reply: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

