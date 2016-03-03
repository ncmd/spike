import base64
import os
import logging

version = "0.4.1.4 - r268 - 2015-03-29"


from flask import Flask
from flask.ext.bootstrap import Bootstrap

import spike.views
from spike.views import *
from spike.model import db


def create_app(config_filename=''):
    logging.info("Spike app.init()")

    app = Flask(__name__)

    if config_filename != "":
        app.config.from_pyfile(config_filename)

    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = base64.b64encode(os.urandom(128))

    app.config["SQLALCHEMY_BINDS"] = {
        'rules': 'sqlite:///rules.db',
        'settings': 'sqlite:///settings.db',
    }

    db.init_app(app)
    db.app = app

    spike.bootstrap = Bootstrap(app)  # add bootstrap templates and css

    # add blueprints
    app.register_blueprint(spike.views.default.default, templates_folder='templates')
    app.register_blueprint(spike.views.rules.rules, templates_folder='templates')
    app.register_blueprint(spike.views.settings.settings, templates_folder='templates')
    app.register_blueprint(spike.views.docs.docs, templates_folder='templates')

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
    try:
        return value.split(":")[0:2]
    except:
        return value, 8


def f_mzsplit(value):
    try:
        return value.split("|")
    except:
        return [value]

