import os
import logging

from flask import current_app, Blueprint, render_template, request, redirect, flash

from spike.model import *

settings = Blueprint('settings', __name__, url_prefix='/settings')


@settings.route("/")
def index():
    _settings = Settings.query.order_by(Settings.name).all()
    if not _settings:
        return redirect("/rules")
    return render_template("settings/index.html", settings=_settings)


@settings.route("/mz")
def mz_index():
    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").order_by(ValueTemplates.value).all()
    if not mz:
        return redirect("/settings")
    return render_template("settings/mz.html", mz=mz)


@settings.route("/sql", methods=["GET", "POST"])
def execute_sql():
    res = []
    sqle = ""

    if request.method == "POST":
        rsql = request.form
        sqle = []
        out = 0
        for s in rsql["sql"].split("\n"):
            s = s.strip()
            if len(s) < 20:
                flash("query is too short", "error")
                return redirect("/settings/sql")
            if not s.endswith(';'):  # append the missing ';'
                s += ' ;'
            if s[0:10].find("select") > -1:
                out = 1
            sqle.append(s)
        if out == 1:
            try:
                res = db.session.execute("\n".join(sqle), bind=db.get_engine(current_app, 'rules')).fetchall()
            except:
                flash("ERROR while trying to execute : %s" % ("\n".join(sqle)), "error")
        else:
            db.session.execute("\n".join(sqle), bind=db.get_engine(current_app, 'rules'))
            db.session.commit()
            res = [("OK", "\n".join(sqle))]
    return render_template("settings/sql.html", res=res, sqlval="\n".join(sqle))


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
    except:
        flash("ERROR while trying to delete : %s" % dmz.value, "error")
    return redirect("/settings/mz")


@settings.route("/mz/new", methods=["POST"])
def mz_new():
    db.session.add(ValueTemplates("naxsi_mz", request.form["nmz"]))
    db.session.commit()
    flash("Updated MZ: %s" % request.form["nmz"], "success")
    return redirect("/settings/mz")


@settings.route("/scores")
def score_index():
    sc = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").order_by(ValueTemplates.value).all()
    if not sc:
        return redirect("/settings")
    return render_template("settings/scores.html", scores=sc)


@settings.route("/scores/new", methods=["POST"])
def score_new():
    if not request.form["nscore"].startswith("$"):
        request.form["nscore"] = '$' + request.form["nscore"]

    db.session.add(ValueTemplates("naxsi_score", request.form["nscore"].upper()))
    db.session.commit()
    flash("Updated Score: %s" % request.form["nscore"], "success")
    return redirect("/settings/scores")


@settings.route("/scores/del", methods=["POST"])
def scores_del():
    dsc = ValueTemplates.query.filter(ValueTemplates.id == request.form["scid"]).first()
    if not dsc:
        flash("Nothing found in %s " % (request.form["scid"]), "error")
        return redirect("/settings/scores")
    db.session.delete(dsc)

    try:
        db.session.commit()
        flash("OK: deleted %s " % dsc.value, "success")
    except:
        flash("ERROR while trying to delete : %s" % dsc.value, "error")
    return redirect("/settings/scores")


@settings.route("/update")
def mz_update():
    flash("OK: update ", "success")
    return render_template("layouts/pre.html", text="".join(os.popen("./server update")), title="Spike-Update")


@settings.route("/save", methods=["POST"])
def save_settings():
    s = ''
    for s in request.form:
        sfind = Settings.query.filter(Settings.name == s).first()
        if not sfind:
            logging.error("no value for %s", sfind)
            continue

        if sfind.value != request.form[s]:
            sfind.value = request.form[s]
            db.session.add(sfind)

    flash("Updated setting: %s" % s, "success")
    db.session.commit()
    os.system("touch spike/__init__.py")
    return redirect("/settings")
