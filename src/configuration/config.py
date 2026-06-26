from flask import flask
from db_routing import SessionSQLAlchemy
from flask_cors import CORS
import logging
from urls import V1Version

BLUEPRINT = (
    V1Version().get_blueprint()
)

def create_app():

    app=flask(__name__)
    CORS(app,resources={
        r"/*": {
            "origins":"*"
        }
    })
    db = SessionSQLAlchemy(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    for urls in BLUEPRINT:
        app.register_blueprint(urls)

    logging.basicConfig(level=logging.INFO)

    
    return app

