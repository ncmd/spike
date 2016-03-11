import base64
import os
import logging

from flask import Flask
from flask.ext.bootstrap import Bootstrap

from spike.views import default, rules, docs, rulesets
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
    app.register_blueprint(docs.docs, url_prefix='/docs')

    # register filters
    app.jinja_env.filters['scoresplit'] = f_scoresplit
    app.jinja_env.filters['mzsplit'] = f_mzsplit
    app.jinja_env.globals['version'] = version

    return app


def f_scoresplit(value):
    """
    :param str value: A string of the form "name:score"
    :return list: Return a list of the form [name, score], with score being an int
    """
    return value.split(":")[0:2]


def f_mzsplit(value):
    return value.split("|")

