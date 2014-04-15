from flask import current_app, Blueprint, render_template, abort, request, flash, redirect, url_for
from spike import get_login_manager, get_flask_bcrypt
from spike.forms.login_form import LoginForm
from flask.ext.login import login_user, logout_user, current_user, login_required, session
from time import time, localtime, strftime 


from spike.model import *

import simplejson as json

default = Blueprint('default', __name__, url_prefix = '/')
login_manager = get_login_manager()

@default.route("/")
def index():
  return(redirect("/rules"))

@default.route("/robots.txt")
def robots():

    out = """User-agent: *
Disallow: /
"""

    return Response(out, mimetype='text/plain')

  
#@default.route("login", methods=["GET", "POST"])
@default.route("login/", methods=["GET", "POST"])
def login():
    if not current_user.is_anonymous():
      return redirect(url_for("default.index"))
      
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        user = form.user
        # validate
        login_user(form.user)
        flash("Logged in successfully.")

        create_user_session()

        
#        session
        
        return redirect(request.args.get("next") or url_for("default.index"))
    return render_template("default/login.html", form=form)
    
@default.route('logout/', methods = ["POST"]) 
#@default.route('logout', methods = ["POST"]) 
def logout():
  logout_user()
  return redirect(url_for("default.login"))
  

@login_manager.user_loader
def load_user(userid):
  return User.query.get(userid)

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_user_session_freshness():

  session_update = 1
  # TODO 
  #~ if not mandate_session_update():
    #~ return(0)
  if session_update == 1:
    create_user_session()

def create_user_session():  
  print "> creating session: ", current_user
