
# spike version
version = "0.3.4 - r143 - 2014-03-17"


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
  print "> Spike start"

  # initiate app
  app = Flask(__name__)
  # load config
  if config_filename != "":
    app.config.from_pyfile(config_filename)
  
  sqldb = os.path.abspath(app.config["NAXSI_RULES_DB"])
  sql_raw = app.config["NAXSI_RULES_DB"]
  #~ if not os.path.isfile(sqldb):
    #~ print "YIKES!! cannot find naxsi-rules-db in %s" % sql_raw
    #~ #sys.exit()
  #~ else:
    #~ print "YIKES!! OK naxsi-rules-db in %s" % sql_raw
    
  app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % sqldb
  # import db and initiate
  from spike.model import db
  db.init_app(app)
  
  # add bootstrap templates and css
  spike.bootstrap = Bootstrap(app)
  
  # add bcrypt
  from flaskext.bcrypt import Bcrypt
  spike.flask_bcrypt = Bcrypt(app)

  # incase it is not set 
  try:
    ac = app.config["NAXSI_RULES_OFFSET"]
  except:
    app.config["NAXSI_RULES_OFFSET"] = 20000
  
  # add blueprints
  app.register_blueprint(spike.views.default.default, templates_folder = 'templates')
  app.register_blueprint(spike.views.naxsi_rules.naxsi_rules, templates_folder = 'templates')

  # add LoginManager
  # not yet, kameraden, not yet ... 
  #~ login_manager = get_login_manager()
  #~ login_manager.init_app(app)

  
  # register filters
  app.jinja_env.filters['ctime'] = f_convert_time
  app.jinja_env.filters['dtime'] = f_datetime
  app.jinja_env.filters['scoresplit'] = f_scoresplit
  app.jinja_env.filters['mzsplit'] = f_mzsplit
  
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
  
