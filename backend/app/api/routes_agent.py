from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent_service import generate_agent_response


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
async def chat_with_agent(request: ChatRequest):
    try:
        return await generate_agent_response(request.message)

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        print(f"Agent error: {error}")

        raise HTTPException(
            status_code=502,
            detail="Unable to process the agent request",
        ) from error