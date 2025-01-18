from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from messenger.app.src.agents import DatingAgent
from messenger.app.src.profiles import personal_profile
from typing import Annotated
import logging
from fastapi.requests import Request


logger = logging.getLogger(__name__)


@asynccontextmanager
async def agent_lifespan(app: FastAPI):
    """
    Manage the lifespan of the DatingAgent within the FastAPI app.
    """
    logger.info("Creating DatingAgent on startup...")
    app.state.agent = DatingAgent(
        personal_profile=personal_profile
    )

    async with app.state.agent:
        yield
    logger.info("DatingAgent shutting down...")


def get_dating_agent(request: Request) -> DatingAgent:
    return request.app.state.agent


DatingAgentDep = Annotated[DatingAgent, Depends(get_dating_agent)]
