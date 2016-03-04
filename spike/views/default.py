from flask import Blueprint, redirect, Response, current_app, send_from_directory

default = Blueprint('default', __name__)


@default.route("/")
def index():
    return redirect("/rules")


@default.route("/download")
def download():
    return send_from_directory(directory=current_app.root_path, filename='rules.db', as_attachment=True)

@default.route("/robots.txt")
def robots():
    return Response('User-agent: *\n Disallow: /', mimetype='text/plain')
