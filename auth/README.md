# Auth API

Centralized authentication and authorization system with Role-based permission system
and OAuth 2.0 integration with Google SSO.

Tech stack:
- Nginx
- FastAPI
- Redis
- Postgres


## Creating superuser

CLI can be used to create superuser

```
python src/auth_cli.py createsuperuser
```

## Database schema

Data about user, existing roles, login history and relationship between 
roles and users is stored in PostgreSQL

```mermaid
erDiagram
    USER |o--|{ LOGIN_RECORD : id
    USER |o--|{ USERROLE : id
    ROLE |o--|{ USERROLE : id

    USER {
        uuid id PK
        string login
        string password
        string first_name
        string last_name
        timestamp created_at
    }

    ROLE {
        uuid id PK
        string name
        string descriptuion
    }

    USERROLE {
        uuid user_id
        uuid role_id
    }

    LOGIN_RECORD {
        uuid id PK
        uuid user_id
        timestamp login_at
        string user_agent
    }
```

## Authentication Schema

Receiving token
```mermaid
sequenceDiagram
    participant User
    participant AuthAPI
    participant Postgres

    User ->> AuthAPI: /login with login and password
    AuthAPI ->> Postgres: Check if user exists
    Postgres ->> AuthAPI: User exists

    Note over AuthAPI: Generate token and refresh token

    AuthAPI ->> User: Token and refresh token
```

Using token
```mermaid
sequenceDiagram
    participant User
    participant API
    participant AuthAPI
    participant Redis

    User ->> API: Ask for data and send token
    API ->> AuthAPI: Check token
    activate AuthAPI
    AuthAPI ->> Redis: Check if user logged out
    Redis ->> AuthAPI: No logout
    Note over AuthAPI: Validate token
    AuthAPI ->> API: OK
    deactivate AuthAPI
    API ->> User: data
```

Refresh token
```mermaid
sequenceDiagram
    participant User
    participant AuthAPI
    participant Redis

    User ->> AuthAPI: Refresh token
    AuthAPI ->> Redis: Check if token was used
    activate Redis
    Redis ->> AuthAPI: Not used
    Note over AuthAPI: Validate refresh token
    AuthAPI ->> Redis: Save token as used
    deactivate Redis
    Note over AuthAPI: Generate new pair of tokens
    AuthAPI ->> User: New pair of tokens
```

Logout
```mermaid
sequenceDiagram
    participant User
    participant AuthAPI
    participant Redis

    User ->> AuthAPI: /logout
    AuthAPI ->> Redis: Save auth token to logout, save refresh as used
    AuthAPI --> User: OK
```

## Errors

| Ошибка | Ответ API |
| ------ | --------- |
| Expired token | `401 Unauthorized` |
| Invalid token signature| `401 Unauthorized` |
| Not enough rights to access resource | `403 Forbidden` |
| Username is already taken | `409 Conflict` |
