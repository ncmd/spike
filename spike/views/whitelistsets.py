from time import time, localtime, strftime

from flask import current_app, Blueprint, render_template, request, redirect, flash, Response, url_for

from spike.model import db
from spike.model.naxsi_whitelistsets import NaxsiWhitelistSets
from spike.model.naxsi_whitelist import NaxsiWhitelist


whitelistsets = Blueprint('whitelistsets', __name__)


@whitelistsets.route("/")
def index():
    _wlset = NaxsiWhitelistSets.query.order_by(NaxsiWhitelistSets.name).all()
    return render_template("whitelistsets/index.html", whitelistsets=_wlset)


@whitelistsets.route("/plain/")
@whitelistsets.route("/plain/<int:wid>")
def plain(wid=0):
    if not wid:
        out = ''.join(map(__get_whitelist_for_whitelistset, NaxsiWhitelistSets.query.all()))
    else:
        out = __get_whitelist_for_whitelistset(NaxsiWhitelistSets.query.filter(NaxsiWhitelistSets.id == wid).first())
    return Response(out, mimetype='text/plain')


@whitelistsets.route("/new", methods=["POST"])
def new():
    wname = request.form["wname"].strip().upper()

    if NaxsiWhitelistSets.query.filter(NaxsiWhitelistSets.name == wname).first():
        flash("The whitelist set %s already exists." % wname, "error")
        return redirect(url_for("whitelistsets.index"))

    db.session.add(NaxsiWhitelistSets(wname, "naxsi-whitelistset: %s" % wname, int(time())))
    db.session.commit()

    flash("OK created: %s " % wname, "success")
    return redirect(url_for("whitelistsets.index"))


@whitelistsets.route("/view/<int:wid>")
def view(wid):
    ruleset = NaxsiWhitelistSets.query.filter(NaxsiWhitelistSets.id == wid).first()
    return render_template("rulesets/view.html", r=ruleset, rout=__get_whitelist_for_whitelistset(ruleset))


@whitelistsets.route("/select/<string:selector>", methods=["GET"])
def select(selector):
    wls = NaxsiWhitelist.query.filter(NaxsiWhitelist.whitelistset == selector).order_by(NaxsiWhitelist.wl.desc()).all()
    _selection = "Search wid: %s " % selector
    return render_template("whitelistsets/index.html", whitelistsets=wls, selection=_selection)


@whitelistsets.route("/del/<int:wid>", methods=["POST"])
def remove(wid):
    _wlset = NaxsiWhitelistSets.query.filter(NaxsiWhitelistSets.id == wid).first()
    if _wlset is None:
        flash("The whitelist set %s doesn't exist." % wid, "error")
        return redirect(url_for("whitelistsets.index"))

    db.session.delete(_wlset)
    db.session.commit()

    flash("Successfully deleted %s " % _wlset.name, "success")
    return redirect(url_for("whitelistsets.index"))


def __get_whitelist_for_whitelistset(whitelistset):
    if not whitelistset:
        return ''

    _rules = NaxsiWhitelist.query.filter(
        NaxsiWhitelist.whitelistset == whitelistset.name,
        NaxsiWhitelist.active == 1
    ).all()

    nxruleset = NaxsiWhitelistSets.query.filter(NaxsiWhitelistSets.name == whitelistset.name).first()
    db.session.add(nxruleset)
    db.session.commit()

    text_rules = ''.join(map(str, _rules))

    header = current_app.config["RULESET_HEADER"]
    header = header.replace("RULESET_DESC", whitelistset.name)
    header = header.replace("RULESET_DATE", strftime("%F - %H:%M", localtime(time())))

    return header + text_rules
