import logging

from time import time
from flask import Blueprint, render_template, request, redirect, flash, Response, url_for
from sqlalchemy.exc import SQLAlchemyError

from spike.model import db
from spike.model.naxsi_whitelist import NaxsiWhitelist
from spike.model.naxsi_whitelistsets import NaxsiWhitelistSets
from spike.model.naxsi_rules import NaxsiRules
from spike.model import naxsi_mz

whitelists = Blueprint('whitelists', __name__)


@whitelists.route("/")
def index():
    _wlist = NaxsiWhitelist.query.order_by(NaxsiWhitelist.wid.desc()).all()
    if not _wlist:
        flash("No whitelist found, please create one", "success")
        return redirect(url_for('whitelists.new'))
    return render_template("whitelists/index.html", whitelists=_wlist)


@whitelists.route("/plain/<string:wid>", methods=["GET"])
def plain(wid):
    _wlist = NaxsiWhitelist.query.filter(NaxsiRules.sid == wid).first()
    if not _wlist:
        flash("no rules found, please create one", "error")
        return redirect(url_for('whitelists.index'))
    return Response(_wlist.fullstr(), mimetype='text/plain')


@whitelists.route("/view/<string:wid>", methods=["GET"])
def view(wid):
    _wlist = NaxsiWhitelist.query.filter(NaxsiRules.sid == wid).first()
    if _wlist is None:
        flash("no rules found, please create one", "error")
        return redirect(url_for('whitelists.index'))

    return render_template("rules/view.html", rule=_wlist, rtext=_wlist)


@whitelists.route("/edit/<string:wid>", methods=["GET"])
def edit(wid):
    return redirect(url_for('whitelists.new'))


@whitelists.route("/explain/", methods=["GET", "POST"])
def explain():
    return redirect(url_for('whitelists.new'))


@whitelists.route("/del/<string:wid>", methods=["GET"])
def del_sid(wid):
    return redirect(url_for('whitelists.new'))


@whitelists.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "GET":
        return render_template("misc/whitelist_generator.html")


@whitelists.route('/new', methods=["GET", "POST"])
def new():
    if request.method == "GET":
        _whitelistesets = NaxsiWhitelistSets.query.all()
        return render_template('whitelists/new.html', matchzones=naxsi_mz, whitelistsets=_whitelistesets)

    logging.debug('Posted new request: %s', request.form)
    mz = "|".join(filter(len, request.form.getlist("mz") + request.form.getlist("custom_mz_val")))

    score = request.form.get("score", "")
    score += ':'
    score += request.form.get("score_%s" % request.form.get("score", ""), "")

    wlist = NaxsiWhitelist(wid=request.form.get("id", ""), timestamp=int(time()),
                            whitelistset=request.form.get("whitelistset", ""), mz=mz, active=1,
                            negative=request.form.get("negative", "") == 'checked')

    wlist.validate()

    if wlist.error:
        flash("ERROR: {0}".format(",".join(wlist.error)))
        return redirect("/rules/new")
    elif wlist.warnings:
        flash("WARNINGS: {0}".format(",".join(wlist.warnings)))
    db.session.add(wlist)

    try:
        db.session.commit()
        flash('Created!')
    except SQLAlchemyError as e:
        flash("Error : %s" % e, "error")

    return redirect(url_for('whitelists.index'))