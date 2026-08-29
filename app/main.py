import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from dotenv import load_dotenv

load_dotenv()

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    environment=os.environ.get("APP_ENV", "development"),
    release=os.environ.get("APP_RELEASE", "rag-pipeline:v1"),
    integrations=[
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
    ],
    traces_sample_rate=1.0,
    send_default_pii=False,
)

from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="RAG API")

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "RAG API is running. Visit /docs to test it."}

# @app.get("/sentry-debug")
# async def trigger_error():
#     return 1 / 0