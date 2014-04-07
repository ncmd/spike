from flask import current_app, Blueprint, render_template, abort, request, redirect, url_for, flash, Response 
from flask.ext.login import login_user, logout_user, current_user, login_required
import simplejson as json
import os 
from time import time, localtime, strftime
from uuid import uuid4 


from spike.views import role_required, render_content
from spike import seeds 
from spike.model import *

docs = Blueprint('docs', __name__, url_prefix = '/docs')

@docs.route("/")
def index():
  rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
  if not rules:
    return(redirect("/rules/new"))
    
  return(render_template("rules/index.html", rules = rules))



