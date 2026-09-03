import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent_service import (
    generate_agent_response,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["AI Agent"],
)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class ChatResponse(BaseModel):
    message: str
    model: str
    provider: str
    data_source: str


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat_with_agent(
    request: ChatRequest,
):
    try:
        return await generate_agent_response(
            request.message
        )

    except RuntimeError as error:
        logger.exception(
            "Agent runtime error"
        )

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected agent request error"
        )

        raise HTTPException(
            status_code=502,
            detail="Unable to process the agent request",
        ) from error