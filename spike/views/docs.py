import os
from glob import glob

from flask import Blueprint, render_template, redirect
from spike.views import render_md

docs = Blueprint('docs', __name__, url_prefix='/docs')


@docs.route("/")
def index():
    return render_template("docs/index.html", doc_display=render_md("docs/docs.md"))


@docs.route("/<path:doc_file>")
def display(doc_file=0):
    doc_files = glob("docs/*.md")
    doc_path = os.path.join("docs", doc_file)

    if doc_path in doc_files:
        return render_template("docs/display.html", display=render_md(doc_path))
    return redirect("/docs")
