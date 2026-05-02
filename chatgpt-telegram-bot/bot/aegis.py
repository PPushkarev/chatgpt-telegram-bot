import os
import threading
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

scan_app = FastAPI()
_openai_helper = None


class AegisScanRequest(BaseModel):
    message: str
    token: str = None


def set_openai_helper(helper):
    global _openai_helper
    _openai_helper = helper


@scan_app.post("/webhook/aegis-scan")
async def aegis_scan(request: AegisScanRequest):
    if request.token != os.getenv("AEGIS_SECRET_TOKEN", "secret123"):
        return {"reply": "Unauthorized"}

    response, _, _ = await _openai_helper.get_chat_response(
        chat_id=0,
        query=request.message
    )
    return {"reply": response}


def start_aegis_server():
    uvicorn.run(scan_app, host="0.0.0.0", port=8080, log_level="warning")


def run_in_background(openai_helper):
    set_openai_helper(openai_helper)
    t = threading.Thread(target=start_aegis_server, daemon=True)
    t.start()