# Auth API

Сервис авторизации с системой ролей.

Используемые технологии:
- Nginx
- FastAPI
- Redis
- Postgres

Доступ предоставляется по ролям (RBAC)

## Создание суперпользователя

Для создания суперпользователя можно использовать cli:

```
python src/auth_cli.py createsuperuser
```

## Схема базы данных

Данные о пользователе, существующих ролях, история логинов, а также отношения 
между пользователями и ролями хранятся в Postgres.

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

## Схема аутентификации

Получение токена
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

Использование токена
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

Обновление токена
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

## Обработка ошибок

| Ошибка | Ответ API |
| ------ | --------- |
| Истекший токен | `401 Unauthorized` |
| Неверная подпись токена | `401 Unauthorized` |
| Нет доступа к ресурсу | `403 Forbidden` |
| Имя пользователя уже занято | `409 Conflict` |
