from flask import Flask
from flask_smorest import Api

from api.v1 import events

app = Flask(__name__)
app.config["API_TITLE"] = "Events API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.1.1"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_JSON_PATH"] = "/api/openapi.json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/api/openapi"
app.config["OPENAPI_SWAGGER_UI_URL"] = (
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
)

api = Api(app)


api.register_blueprint(events.router, url_prefix="/ugc")


@app.route("/")
def home():
    return "Hello from Flask app"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=True)
