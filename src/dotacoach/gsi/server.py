import logging
from typing import Optional
from fastapi import FastAPI, Request
from dotacoach.events import EventBus
from .models import GsiPayload
from .parser import diff_to_events

log = logging.getLogger(__name__)

def build_app(bus: EventBus) -> FastAPI:
    app = FastAPI()
    state = {"prev": None}

    @app.post("/gsi")
    async def gsi(request: Request):
        try:
            data = await request.json()
            curr = GsiPayload.model_validate(data)
        except Exception as e:
            log.warning("invalid GSI payload: %s", e)
            return {"ok": True}
        prev: Optional[GsiPayload] = state["prev"]
        for ev in diff_to_events(prev, curr):
            await bus.publish(ev)
        state["prev"] = curr
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app

def serve(bus: EventBus, port: int) -> None:
    import uvicorn
    uvicorn.run(build_app(bus), host="127.0.0.1", port=port, log_level="warning")
