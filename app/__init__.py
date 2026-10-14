"""Application factory for the Appointment Manager."""
import os

from flask import Flask

from . import db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_mapping(
        DATABASE=os.path.join(os.path.dirname(app.root_path), "appointments.db"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.init_db()
    return app
