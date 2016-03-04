from flask import Blueprint, render_template, request, redirect, flash
from sqlalchemy.exc import SQLAlchemyError

from spike.model import db
from spike.model.naxsi_rules import ValueTemplates

settings = Blueprint('settings', __name__)


@settings.route("/mz")
def mz_index():
    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").order_by(ValueTemplates.value).all()
    if not mz:
        return redirect("/settings")
    return render_template("settings/mz.html", mz=mz)


@settings.route("/mz/del", methods=["POST"])
def mz_del():
    dmz = ValueTemplates.query.filter(ValueTemplates.id == request.form["mzid"]).first()
    if not dmz:
        flash("Nothing found in %s " % (request.form["mzid"]), "error")
        return redirect("/settings/mz")

    db.session.delete(dmz)
    try:
        db.session.commit()
        flash("OK: deleted %s " % dmz.value, "success")
    except SQLAlchemyError:
        flash("ERROR while trying to delete : %s" % dmz.value, "error")
    return redirect("/settings/mz")


@settings.route("/mz/new", methods=["POST"])
def mz_new():
    db.session.add(ValueTemplates("naxsi_mz", request.form["nmz"]))
    db.session.commit()
    flash("Updated MZ: %s" % request.form["nmz"], "success")
    return redirect("/settings/mz")


@settings.route("/scores")
def scores_index():
    sc = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").order_by(ValueTemplates.value).all()
    if not sc:
        return redirect("/settings")
    return render_template("settings/scores.html", scores=sc)


@settings.route("/scores/new", methods=["POST"])
def scores_new():
    if not request.form["nscore"].startswith("$"):
        request.form["nscore"] = '$' + request.form["nscore"]

    db.session.add(ValueTemplates("naxsi_score", request.form["nscore"].upper()))
    db.session.commit()
    flash("Updated Score: %s" % request.form["nscore"], "success")
    return redirect("/settings/scores")


@settings.route("/scores/del", methods=["POST"])
def scoress_del():
    dsc = ValueTemplates.query.filter(ValueTemplates.id == request.form["scid"]).first()
    if not dsc:
        flash("Nothing found in %s " % (request.form["scid"]), "error")
        return redirect("/settings/scores")
    db.session.delete(dsc)

    try:
        db.session.commit()
        flash("OK: deleted %s " % dsc.value, "success")
    except SQLAlchemyError:
        flash("ERROR while trying to delete : %s" % dsc.value, "error")
    return redirect("/settings/scores")
