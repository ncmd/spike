from flask import current_app, Blueprint, render_template, abort, request, redirect, url_for, flash, Response 
from flask.ext.login import login_user, logout_user, current_user, login_required
import simplejson as json
import os 
from time import time, localtime, strftime
from uuid import uuid4 
from glob import glob 


from spike.views import role_required, render_content, render_md
from spike import seeds 
from spike.model import *

docs = Blueprint('docs', __name__, url_prefix = '/docs')

@docs.route("/")
def index():

  doc_info = render_md("docs/docs.md")
    
  return(render_template("docs/index.html", doc_display = doc_info))


@docs.route("/<path:doc_file>")
def display(doc_file=0):

  doc_files = glob("docs/*.md")
  doc_path = "docs/%s" % doc_file
  if doc_path in doc_files:
    display = render_md(doc_path)
    return(render_template("docs/display.html", display = display))

  return(redirect("/docs"))

