# Online-cinema

A microservices-based platform demonstrating the core functionality of a streaming service.

Services include:
1. Admin panel
    * Web interface for content management and data operations
    * Technologies: Django, PostgreSQL, Nginx
2. ETL pipeline
    * Automated data synchronization between PostgreSQL and Elasticsearch
    * Error handling and retry mechanisms
    * Technologies: Python, PostgreSQL, Elasticsearch
3. Movies API
    * RESTful endpoints for content discovery and search
    * Advanced filtering and sorting capabilities
    * Full-text search powered by Elasticsearch
    * Cashing layer for better performance
    * Request limit for better performance
    * Technologies: FastAPI, Elasticsearch, Redis
4. Auth API
    * Centralized authentication and authorization system
    * Secure JWT-based token management
    * OAuth 2.0 integration with Google SSO
    * Role-based permission system
    * API endpoints for user management
    * Technologies: FastAPI, PostgreSQL, Redis
5. [Jaeger](https://github.com/jaegertracing/jaeger)
    * Tracing


## Launching services


Movies API:
```bash
docker compose up --build -d nginx-movies-api movies-api redis-api elasticsearch
```

Launching auth API:

`export OAUTHLIB_INSECURE_TRANSPORT=1` for testing

```bash
docker compose up --build -d nginx-auth auth-api postgres-auth redis-auth
```

Launching ETL:
```bash
docker compose up --build -d database elasticsearch redis-etl etl
```

Launching Admin:
```bash
docker compose up --build -d admin-service nginx-admin postgres-movies
```

When each service starts, a script is executed that checks the connection to 
external services. Only after the connection is established does the main service start.


## Testing

The tests are run in the same image that is used for the API. Therefore, it is
necessary to first create the image and then run the tests.

Running tests for movies-api
```
cd app/tests/functional && docker compose up
```

Running tests for auth-api
```
cd auth/tests/functional && docker compose up
```
