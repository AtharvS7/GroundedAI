"""Structured logging middleware using structlog."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all requests with timing and metadata."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()

        logger.info(
            "request_started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "client": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)

            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Duration-Ms"] = str(duration_ms)
            return response

        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_ms": duration_ms,
                },
            )
            raise
