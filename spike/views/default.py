from flask import Blueprint, redirect, Response


default = Blueprint('default', __name__, url_prefix='/')


@default.route("/")
def index():
    return redirect("/rules")


@default.route("/robots.txt")
def robots():
    return Response('User-agent: *\n Disallow: /', mimetype='text/plain')
