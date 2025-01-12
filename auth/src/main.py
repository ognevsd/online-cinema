import logging
from redis.asyncio import Redis
import uvicorn

from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)

from api.v1 import users, roles
from db import redis
from core.config import settings
from core.logger import LOGGING


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis(host=settings.redis_host, port=settings.redis_port)
    yield
    await redis.redis.close()


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    docs_url="/api/openapi",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)
app.add_middleware(
    SessionMiddleware, secret_key=settings.session_middleware_key
)
add_pagination(app)

if not settings.debug:
    origins = ["http://localhost", "http://127.0.0.1", "http:/auth-tests"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "auth-tests"],
    )
    app.add_middleware(HTTPSRedirectMiddleware)

    def configure_tracer() -> None:
        resource = Resource(attributes={"service.name": "auth-api"})
        trace.set_tracer_provider(TracerProvider(resource=resource))

        otlp_exporter = OTLPSpanExporter(
            endpoint=f"http://{settings.jaeger_host}:{settings.jaeger_port}/v1/traces"
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

    configure_tracer()

    @app.middleware("http")
    async def before_request(request: Request, call_next):
        response = await call_next(request)
        request_id = request.headers.get("X-Request-Id")
        print(request_id)
        if not request_id:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        return response

    FastAPIInstrumentor.instrument_app(app)

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
        reload=True,
    )
