from flask import Flask

from app.extensions import db, migrate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models
    from app.routes import main

    app.register_blueprint(main)

    return app