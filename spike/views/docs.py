import os
import glob
import markdown

try:  # python3 ftw !
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from flask import Blueprint, render_template, redirect

docs = Blueprint('docs', __name__)


def __render_md(md_file):
    """
    :param str md_file: Path to a markdown file
    :return str: html rendering of the `md_file` markdown file
    """
    ret = StringIO()
    markdown.markdownFromFile(input=md_file, output=ret, encoding='utf-8')
    return ret.getvalue()


@docs.route("/")
def index():
    return render_template("docs/index.html", data=__render_md("docs/docs.md"))


@docs.route("/<path:doc_file>")
def display(doc_file):
    if doc_file == 'README.md':
        doc_path = doc_file
    else:
        doc_path = os.path.join("docs", doc_file)
        if doc_path not in glob.glob("docs/*.md"):
            return redirect('/docs')
    return render_template("docs/index.html", data=__render_md(doc_path), title='<a href="/docs">Spike - Docs</a>')
