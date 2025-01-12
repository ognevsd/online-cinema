from json import JSONDecodeError
import uvicorn
import logging
import datetime as dt

from contextlib import asynccontextmanager
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis


from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)

from api.v1 import films
from api.v1 import genres
from api.v1 import persons
from core.config import settings
from core.logger import LOGGING
from services.auth_service import get_username
from db import elastic, redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis(host=settings.redis_host, port=settings.redis_port)
    elastic.es = AsyncElasticsearch(hosts=[settings.elastic_url])
    yield
    await redis.redis.close()
    await elastic.es.close()


app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.project_version,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    period = dt.timedelta(seconds=60)
    print(request.headers)
    if "authorization" not in request.headers:
        user_key = request.headers.get("x-real-ip")
    else:
        try:
            user_key = await get_username(request.headers["authorization"])
        except JSONDecodeError:
            user_key = request.headers.get("x-real-ip")

    if user_key is None:
        user_key = request.headers.get("x-real-ip")

    key = f"rate-limit:{user_key}"
    redis_client = await redis.get_redis()

    if await redis_client.setnx(key, settings.request_limit_per_minute):
        print("Setting new key")
        await redis_client.expire(key, int(period.total_seconds()))

    requests_left = await redis_client.get(key)
    if requests_left and int(requests_left) > 0:
        await redis_client.decrby(key, 1)
    else:
        return ORJSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests, please wait"},
        )

    response = await call_next(request)
    # print(response)

    return response


if not settings.debug:

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

    def configure_tracer() -> None:
        resource = Resource(attributes={"service.name": "movies-api"})
        trace.set_tracer_provider(TracerProvider(resource=resource))

        otlp_exporter = OTLPSpanExporter(
            endpoint=f"http://{settings.jaeger_host}:{settings.jaeger_port}/v1/traces"
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

    configure_tracer()

    FastAPIInstrumentor.instrument_app(app)

app.include_router(
    films.router,
    prefix="/api/v1/films",
    tags=[
        "films",
    ],
)
app.include_router(
    genres.router,
    prefix="/api/v1/genres",
    tags=[
        "genres",
    ],
)
app.include_router(
    persons.router,
    prefix="/api/v1/persons",
    tags=[
        "persons",
    ],
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
        reload=True,
    )
