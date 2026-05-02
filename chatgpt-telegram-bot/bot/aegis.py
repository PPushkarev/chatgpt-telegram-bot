import os
import threading
import uvicorn
import uuid  # Добавляем для уникальных ID
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Сервер для сканера
scan_app = FastAPI()
_openai_helper = None


class AegisScanRequest(BaseModel):
    message: str
    token: str = None


def set_openai_helper(helper):
    global _openai_helper
    _openai_helper = helper


@scan_app.post("/webhook/aegis-scan")
async def aegis_scan_endpoint(request: AegisScanRequest):
    # 1. Проверка токена
    if request.token != os.getenv("AEGIS_SECRET_TOKEN", "12345"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2. Создаем изолированный ID для этого конкретного теста
    # Это предотвращает "загрязнение" истории чата (как в твоем Scenario A)
    scan_session_id = f"test_{uuid.uuid4().hex[:8]}"

    # 3. Прямой вызов "мозга" бота
    # Используем корректную распаковку (2 значения)
    answer, _ = await _openai_helper.get_chat_response(
        chat_id=scan_session_id,
        query=request.message
    )

    return {"reply": answer}


def start_aegis_server():
    # Railway сам пробросит порт, если он указан как 8080 или взят из env
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(scan_app, host="0.0.0.0", port=port, log_level="warning")


def run_in_background(openai_helper):
    set_openai_helper(openai_helper)
    t = threading.Thread(target=start_aegis_server, daemon=True)
    t.start()