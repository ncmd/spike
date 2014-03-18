from flask import current_app, Blueprint, render_template, abort, request, redirect, url_for, flash, Response 
from flask.ext.login import login_user, logout_user, current_user, login_required
import simplejson as json
import os 
from time import time, localtime, strftime
from uuid import uuid4 


from spike.views import role_required
from spike import seeds 
from spike.model import *

settings = Blueprint('settings', __name__, url_prefix = '/settings')

@settings.route("/")
def index():
  settings = Settings.query.order_by(Settings.name).all()
  if not settings:
    return(redirect("/rules"))
  return(render_template("settings/index.html", settings = settings))

@settings.route("/save", methods = ["POST"])
def save_settings():
  
  sform = request.form
  for s in sform:
    sfind = Settings.query.filter(Settings.name == s).first()
    if not sfind:
      print "> no value for %s" % sfind
      continue
    if sfind.value != sform[s]:
      sfind.value = sform[s]
      db.session.add(sfind)
      flash("Updated setting: %s" % s, "success")
  db.session.commit()
  os.system("touch spike/__init__.py")
  return(redirect("/settings"))
  

@settings.route("/<path:szone>")
def szone(szone=0):
  return(render_template("notyet.html", text = ""))

