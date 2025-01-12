# Alembic settings

За миграции в приложении отвечает Alembic. Для того чтобы применить последнюю
миграцию, выполните следующую команду:

```
alembic upgrade head
```

`c2180dbab55e` - последняя версия миграции на данный момент.

Для того чтобы Alembic нашел все модули, убедитесь, что `src/` находится в 
`PYTHONPATH`.

Для того чтобы добавить `src/` в `PYTHONPATH`, выполните следующую команду в
корне сервиса:
```
cd src && export PYTHONPATH="${PYTHONPATH}:$PWD"
```

Для того чтобы применить следующую миграцию, выполните:
```
alembic revision --autogenerate -m "Describe changes"
```
