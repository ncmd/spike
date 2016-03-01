from glob import glob

from flask import Blueprint, render_template, redirect

from spike.views import render_md

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

