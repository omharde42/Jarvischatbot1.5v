import time
import os
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("server")

# Initialize FastAPI app
app = FastAPI(
    title="JARVIS AI Assistant",
    description="Voice + System-Control Desktop AI Assistant",
    version="2.0.0"
)

# Request Models
class CommandRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None

class ConfirmationRequest(BaseModel):
    confirmation_token: str
    confirmed: bool

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/api/status")
async def get_system_status():
    from skills import system
    telemetry = system.get_telemetry()
    return JSONResponse(content={
        "status": "ok",
        "timestamp": time.time(),
        "telemetry": telemetry
    })

@app.post("/api/execute")
async def execute_command(req: CommandRequest):
    from app.intent import parse_and_execute
    try:
        result = await parse_and_execute(req.command, req.context)
        return JSONResponse(content=result)
    except Exception as e:
        logger.exception("Error executing command: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "An internal error occurred.",
                "spoken_response": "An internal error occurred while executing the command."
            }
        )

@app.post("/api/confirm")
async def confirm_action(req: ConfirmationRequest):
    from app.safety import safety_engine
    result = await asyncio.to_thread(safety_engine.process_confirmation, req.confirmation_token, req.confirmed)
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
