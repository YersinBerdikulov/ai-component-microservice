from dotenv import load_dotenv
load_dotenv()

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scaffold, predict, report, assess_vl, chat
from app.middleware.logging import RequestLoggingMiddleware

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)

app = FastAPI(
    title="AI Simulator Service",
    description="AI microservice for educational data analysis simulator",
    version="1.0.0",
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scaffold.router, prefix="/api/v1", tags=["scaffold"])
app.include_router(predict.router, prefix="/api/v1", tags=["predict"])
app.include_router(report.router, prefix="/api/v1", tags=["report"])
app.include_router(assess_vl.router, prefix="/api/v1", tags=["assess-vl"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
