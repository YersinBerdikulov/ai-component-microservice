import json
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ai_service")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.monotonic()

        body_bytes = await request.body()
        # Re-inject body so the route handler can still read it
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000)

        log_record = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }

        # Extract teacher_id / scenario_id from body for pilot study tracking
        if body_bytes:
            try:
                body = json.loads(body_bytes)
                for field in ("teacher_id", "scenario_id", "vl_level"):
                    if field in body:
                        log_record[field] = body[field]
            except Exception:
                pass

        logger.info(json.dumps(log_record, ensure_ascii=False))
        return response
