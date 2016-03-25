from flask import Blueprint, redirect, Response, current_app, send_from_directory, request, url_for
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime

from spike.model.naxsi_rules import NaxsiRules

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


@default.route('/rules.atom')
def atom():
    feed = AtomFeed(title='Recent rules', feed_url=request.url, url=request.url_root, author='Spike',
                    icon=url_for('static', filename='favicon.ico'))
    _rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).limit(15).all()
    if _rules:
        for rule in _rules:
            feed.add(rule.msg, str(rule), updated=datetime.fromtimestamp(rule.timestamp), id=rule.sid)
    return feed.get_response()
