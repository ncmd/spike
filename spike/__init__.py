
# spike version
version = "0.3.10 - r143 - 2014-04-04"


login_manager = None

def get_login_manager():
  from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
  if spike.login_manager == None:
    spike.login_manager = LoginManager()
  return spike.login_manager
  
flask_bcrypt = None
  
def get_flask_bcrypt():
    return spike.flask_bcrypt  

from flask import Flask, app, session, redirect, url_for, escape, request
import spike.views
from spike.views import *
from flask.ext.bootstrap import Bootstrap
from setuptools.command import easy_install
from time import strftime, localtime, time
import os, subprocess, sys


def spike_version():
  return(version)

def create_app(config_filename): 
  print "> Spike app.init()"

  # initiate app
  app = Flask(__name__)
  # load config
  if config_filename != "":
    app.config.from_pyfile(config_filename)

  app.config["SQLALCHEMY_BINDS"] = {
    'rules':        'sqlite:///rules.db',
    'settings':     'sqlite:///settings.db',
  }

  from spike.model import db
  db.init_app(app)
  
  # add bootstrap templates and css
  spike.bootstrap = Bootstrap(app)
  
  # add bcrypt
  from flaskext.bcrypt import Bcrypt
  spike.flask_bcrypt = Bcrypt(app)

  # add blueprints
  app.register_blueprint(spike.views.default.default, templates_folder = 'templates')
  app.register_blueprint(spike.views.naxsi_rules.naxsi_rules, templates_folder = 'templates')
  app.register_blueprint(spike.views.settings.settings, templates_folder = 'templates')
  app.register_blueprint(spike.views.docs.docs, templates_folder = 'templates')

  # add LoginManager
  # not yet, kameraden, not yet ... 
  #~ login_manager = get_login_manager()
  #~ login_manager.init_app(app)

  
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
    return(sc[0], sc[1])
  except:
    return(value, 8)
  

def f_mzsplit(value):
  
  try:
    mc = value.split("|")
    return(mc)
  except:
    return([value])  
  

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
  return(mzu)
  
  
