import base64
import os
import logging

from flask import Flask
from flask_bootstrap import Bootstrap

from spike.views import default, rules, rulesets, sandbox, whitelists, whitelistsets
from spike.model import db

version = "0.5 "


def create_app(config_filename=''):
    logging.info("Spike app.init()")

    app = Flask(__name__)

    if config_filename:
        app.config.from_pyfile(config_filename)

    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = base64.b64encode(os.urandom(128))

    app.config["SQLALCHEMY_BINDS"] = {'rules': 'sqlite:///rules.db'}

    db.init_app(app)
    db.app = app

    Bootstrap(app)  # add bootstrap templates and css

    # add blueprints
    app.register_blueprint(default.default)
    app.register_blueprint(rules.rules, url_prefix='/rules')
    app.register_blueprint(rulesets.rulesets, url_prefix='/rulesets')
    app.register_blueprint(sandbox.sandbox, url_prefix='/sandbox')
    app.register_blueprint(whitelists.whitelists, url_prefix='/whitelists')
    app.register_blueprint(whitelistsets.whitelistsets, url_prefix='/whitelistsets')

    # register filters
    app.jinja_env.globals['version'] = version

    return app
