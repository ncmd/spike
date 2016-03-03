import os
import glob
import markdown
import StringIO

from flask import Blueprint, render_template, redirect

docs = Blueprint('docs', __name__, url_prefix='/docs')


def __render_md(md_file):
    """
    :param str md_file: Path to a markdown file
    :return str: html rendering of the `md_file` markdown file
    """
    if not os.path.isfile(md_file):
        return ''
    ret = StringIO.StringIO()
    markdown.markdownFromFile(input=md_file, output=ret)
    return ret.getvalue()


@docs.route("/<path:doc_file>")
def display(doc_file=''):
    if not doc_file:
        return render_template("docs/index.html", doc_display=__render_md("docs/docs.md"))

    doc_path = os.path.join("docs", doc_file)
    if doc_path in glob.glob("docs/*.md"):
        return render_template("docs/display.html", display=__render_md(doc_path))
    return redirect("/docs")
