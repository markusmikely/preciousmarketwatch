"""
PMW Bridge — FastAPI HTTP/WebSocket service.

Exposes port 8000 (or PORT from Railway).
"""
from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    print("PMW Bridge starting...")


@app.get("/")
async def root():
    return {"service": "pmw-bridge", "status": "running"}
