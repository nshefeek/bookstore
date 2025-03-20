import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger = get_logger("api.request")
        request_id = str(uuid.uuid4())

        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=request.query_params,
            request_id=request_id,
            client_ip=request.client.host,
        )

        start_time = time.time()
        try:
            response: Response = await call_next(request)
            duration = time.time() - start_time

            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                request_id=request_id,
                duration=duration,
            )
            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(
                "Request failed",
                method=request.method,
                path=request.url.path,
                request_id=request_id,
                duration=duration,
                exception=str(e),
            )
            raise
