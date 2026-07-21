from flask import Flask, jsonify
from configuration.db_routing import db
from flask_cors import CORS
import logging
from configuration.urls import V1Version
from configuration.variables import POSTGRES_DB_URI
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

BLUEPRINT = [
    V1Version().get_blueprint()
]

def create_app():

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = POSTGRES_DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    CORS(app, resources={
        r"/*": {
            "origins":"*"
        }
    })
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
        except OperationalError:
            logging.exception(
                "Database is unavailable; skipping schema creation during startup."
            )

    for urls in BLUEPRINT:
        app.register_blueprint(urls)

    logging.basicConfig(level=logging.INFO)

    @app.route("/health", methods=["GET"])
    def health():
        db_ok = True
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db_ok = False

        status_code = 200 if db_ok else 503
        return jsonify({
            "status": "ok" if db_ok else "degraded",
            "database": "up" if db_ok else "down",
        }), status_code

    return app
