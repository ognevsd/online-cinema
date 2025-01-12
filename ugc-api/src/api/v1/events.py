from http import HTTPStatus
from flask.views import MethodView
from flask_smorest import Blueprint

import marshmallow as ma

router = Blueprint("events", "events")


class EventSchema(ma.Schema):
    name = ma.fields.String()


@router.route("/click")
class Click(MethodView):
    @router.arguments(EventSchema)
    @router.response(status_code=HTTPStatus.OK, schema=EventSchema)
    def post(self, parameters):
        return parameters


class PageView(MethodView): ...


class CustomEvent(MethodView): ...
