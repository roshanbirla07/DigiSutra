from flask import Flask, jsonify
from configuration.db_routing import db
from flask_cors import CORS
import logging
import os
from configuration.urls import V1Version
from configuration.variables import CORS_ALLOWED_ORIGINS, LOG_LEVEL, POSTGRES_DB_URI
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

BLUEPRINT = [
    V1Version().get_blueprint()
]

def _schema_bootstrap_enabled():
    return os.getenv("ENABLE_DB_CREATE_ALL", "").lower() in {"1", "true", "yes"}


def create_app():

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = POSTGRES_DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    allowed_origins = [origin.strip() for origin in CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    db.init_app(app)
    if _schema_bootstrap_enabled():
        with app.app_context():
            try:
                db.create_all()
            except OperationalError:
                logging.exception(
                    "Database is unavailable; skipping schema creation during startup."
                )

    for urls in BLUEPRINT:
        app.register_blueprint(urls)

    logging.basicConfig(level=getattr(logging, str(LOG_LEVEL or "INFO").upper(), logging.INFO))

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
