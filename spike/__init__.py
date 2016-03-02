import base64
import os

version = "0.4.1.4 - r268 - 2015-03-29"

flask_bcrypt = None
def get_flask_bcrypt():
    return spike.flask_bcrypt


import string
from time import strftime, localtime, time

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.bcrypt import Bcrypt

import spike.views
from spike.views import *
from spike.model import db


def create_app(config_filename):
    print "> Spike app.init()"

    # initiate app
    app = Flask(__name__)
    # load config
    if config_filename != "":
        app.config.from_pyfile(config_filename)

    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = base64.b64encode(os.urandom(128))

    app.config["SQLALCHEMY_BINDS"] = {
        'rules': 'sqlite:///rules.db',
        'settings': 'sqlite:///settings.db',
    }

    db.init_app(app)

    spike.bootstrap = Bootstrap(app)  # add bootstrap templates and css
    spike.flask_bcrypt = Bcrypt(app)  # add bcrypt

    # add blueprints
    app.register_blueprint(spike.views.default.default, templates_folder='templates')
    app.register_blueprint(spike.views.rules.rules, templates_folder='templates')
    app.register_blueprint(spike.views.settings.settings, templates_folder='templates')
    app.register_blueprint(spike.views.docs.docs, templates_folder='templates')

    # add LoginManager
    # not yet, kameraden, not yet ...
    # ~ login_manager = get_login_manager()
    # ~ login_manager.init_app(app)

    # register filters
    app.jinja_env.filters['ctime'] = f_convert_time
    app.jinja_env.filters['dtime'] = f_datetime
    app.jinja_env.filters['scoresplit'] = f_scoresplit
    app.jinja_env.filters['mzsplit'] = f_mzsplit
    app.jinja_env.filters['mzpop'] = f_mzpop
    app.jinja_env.globals['version'] = version

    return app


def f_convert_time(value, format='%d. %b %H:%M'):
    return value.strftime(format)


def f_datetime(value, format='%F %H:%M'):
    try:
        return strftime(format, localtime(float(str(value))))
    except:
        return strftime(format, localtime(time()))


def f_scoresplit(value):
    try:
        sc = value.split(":")
        return (sc[0], sc[1])
    except:
        return (value, 8)


def f_mzsplit(value):
    try:
        mc = value.split("|")
        return (mc)
    except:
        return ([value])


def f_mzpop(mza, value):
    print "mza:"
    print mza
    print "value:"
    print value
    mzu = []
    for m in mza:
        if m == value:
            pass
        else:
            mzu.append(m)
    print mzu
    return (mzu)
