
version = "0.4.1.4 - r268 - 2015-03-29"


login_manager = None

def get_login_manager():
  from flask.ext.login import LoginManager
  if spike.login_manager == None:
    spike.login_manager = LoginManager()
  return spike.login_manager
  
flask_bcrypt = None



def get_flask_bcrypt():
  return spike.flask_bcrypt


import string
from time import strftime, localtime, time

from flask import Flask
from flask.ext.bootstrap import Bootstrap

import spike.views
from spike.views import *


def spike_version():
  return(version)

def create_app(config_filename): 
  print "> Spike app.init()"

  # initiate app
  app = Flask(__name__)
  # load config
  if config_filename != "":
    app.config.from_pyfile(config_filename)

  if not app.config["SECRET_KEY"]:
    app.config["SECRET_KEY"] = random_string()

  app.config["SQLALCHEMY_BINDS"] = {
    'rules':        'sqlite:///rules.db',
    'settings':     'sqlite:///settings.db',
  }

  from spike.model import db
  db.init_app(app)
  
  # add bootstrap templates and css
  spike.bootstrap = Bootstrap(app)
  
  # add bcrypt
  from flask.ext.bcrypt import Bcrypt
  spike.flask_bcrypt = Bcrypt(app)

  # add blueprints
  app.register_blueprint(spike.views.default.default, templates_folder = 'templates')
  app.register_blueprint(spike.views.rules.rules, templates_folder = 'templates')
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
  
def random_string(l=128):
    #
    # see http://security.stackexchange.com/a/41503/27702
    # credits: Brendan Long
    #
    # func stolen from https://makepw.com
    #
    from random import SystemRandom
    
    rng = SystemRandom()
    

    allchars = string.ascii_letters + string.digits
    
    
    try:
        passwordLength = int(l)
    except:
        #user didn't specify a length.  that's ok, just use 8
        passwordLength = 32

    # not less 
    if passwordLength < 8:
        passwordLength = 32
    elif passwordLength > 128:
        passwordLength = 32

    pw = "".join([rng.choice(allchars) for i in range(passwordLength)])
    
    return(pw)


