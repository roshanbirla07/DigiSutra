from flask import flask
from db_routing import SessionSQLAlchemy
from flask_cors import CORS

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
    
    return app

