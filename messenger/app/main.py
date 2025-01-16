import logging
from fastapi import FastAPI
from messenger.app.dependencies import agent_lifespan
from messenger.app.v1.endpoints import message_router
import uvicorn


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Messenger Service API",
    description="Api service for AgenticTinder bot.",
    version="0.1.0",
    lifespan=agent_lifespan,
    servers=[
        {"url": "/", "description": "Local Server"},
    ],
)


@app.get("/", include_in_schema=False)
async def root():
    return {"status": "ok"}


@app.get("/health", include_in_schema=False)
async def health():
    return {"health": "ok"}

app.include_router(
    message_router,
    prefix="/v1",
    tags=["messenger"],
)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)