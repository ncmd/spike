from flask import Blueprint, redirect, Response, current_app, send_from_directory, request
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
    feed = AtomFeed('Recent rules', feed_url=request.url, url=request.url_root)
    _rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).limit(15).all()
    if _rules:
        for rule in _rules:
            feed.add(title=rule.msg,
                     entires=unicode(rule.fullstr()),
                     content_type='text',
                     updated=datetime.fromtimestamp(rule.timestamp),
                     id=rule.sid)
    return feed.get_response()
