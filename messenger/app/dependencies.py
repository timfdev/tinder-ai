from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from messenger.app.src.agent import DatingAgent
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
    app.state.agent = DatingAgent()

    try:
        yield
    finally:
        logger.info("DatingAgent shutting down...")
        # Clean up any resources if needed
        if hasattr(app.state.agent, 'memory'):
            app.state.agent.memory.clear()


def get_dating_agent(request: Request) -> DatingAgent:
    return request.app.state.agent


DatingAgentDep = Annotated[DatingAgent, Depends(get_dating_agent)]
