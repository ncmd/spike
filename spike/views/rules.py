import logging
import re
import string
import os


from time import time
from flask import Blueprint, render_template, request, redirect, flash, Response, url_for, current_app
#from sqlalchemy.exc import IntegrityError
from pysqlite2.dbapi2 import IntegrityError

from spike.model import db
from spike.model.naxsi_rules import NaxsiRules
from spike.model.naxsi_rulesets import NaxsiRuleSets
from spike.model import naxsi_mz, naxsi_score



from werkzeug import secure_filename

rules = Blueprint('rules', __name__)


@rules.route("/")
def index():
    _rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
    if not _rules:
        flash("No rules found, please create one", "success")
        return redirect(url_for("rules.new"))
    return render_template("rules/index.html", rules=_rules)


@rules.route("/plain/<int:sid>", methods=["GET"])
def plain(sid):
    _rule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not _rule:
        flash("No rules found, please create one", "error")
        return redirect(url_for("rules.new"))
    return Response(_rule.fullstr(), mimetype='text/plain')


@rules.route("/view/<int:sid>", methods=["GET"])
def view(sid):
    _rule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if _rule is None:
        flash("no rules found, please create one", "error")
        return redirect(url_for("rules.index"))
    return render_template("rules/view.html", rule=_rule, rtext=_rule)


@rules.route("/search/", methods=["GET"])
def search():
    terms = request.args.get('s', '')

    if len(terms) < 2:
        return redirect(url_for("rules.index"))

    # No fancy injections
    whitelist = set(string.ascii_letters + string.digits + ':-_ ')
    filtered = ''.join(filter(whitelist.__contains__, terms))

    if filtered.isdigit():  # get rule by id
        _rules = db.session.query(NaxsiRules).filter(NaxsiRules.sid == int(filtered))
    else:
        cve = re.search('cve:\d{4}-\d{4,}', filtered, re.IGNORECASE)  # search by CVE

        expression = '%' + filtered + '%'
        _rules = db.session.query(NaxsiRules).filter(
            db.or_(
                NaxsiRules.msg.like(expression),
                NaxsiRules.rmks.like(expression),
                NaxsiRules.detection.like(expression)
            )
        )
        if cve:
            _rules.filter(NaxsiRules.msg.like('%' + cve.group() + '%'))
    _rules = _rules.order_by(NaxsiRules.sid.desc()).all()
    return render_template("rules/index.html", rules=_rules, selection="Search: %s" % filtered, lsearch=terms)


@rules.route("/import", methods=["POST", "GET"])
def import_rules():
    """
    Import rules to an existing ruleset from a file.
    :return:
    """
    _rulesets = NaxsiRuleSets.query.all()

    if request.method == "GET":
        return render_template("rules/import.html", rulesets=_rulesets)
    success_imports = 0
    potential_imports = 0
    upfile = request.files['file']
    ruleset = request.form.get("ruleset", "")
    flash("Importing in ruleset {0}".format(ruleset))
    if not ruleset or not upfile:
        flash("missing rule file and/or ruleset name.")
        return redirect(url_for("rules.new"))

    filename = secure_filename(upfile.filename)
    upfile.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    raw = open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), "r")
    for potential_rule in raw.readlines():
        potential_rule = potential_rule.strip()
        # Save ourselves some time by not trying to import comments
        if potential_rule.startswith("#"):
            continue
        potential_imports += 1
        tmp = NaxsiRules(ruleset=ruleset, active=1)
        if tmp.parse_rule(potential_rule) is False:
            print "Parsing failed for '{}'".format(potential_rule)
            print "errors : {0}".format(tmp.error)

            continue
        else:
            db.session.add(tmp)
            try:
                db.session.commit()
                success_imports += 1
            except:
                #pysqlite2.dbapi2.IntegrityError
                db.session.rollback()
                flash("Rule #{0} has no unique ID, skip".format(tmp.sid))
    flash("Imported {0} out of {1} rules in ruleset {2}".format(success_imports, potential_imports, ruleset))
    return render_template("rules/import.html", rulesets=_rulesets)


@rules.route("/new", methods=["GET", "POST"])
def new():
    latest_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
    if latest_sid is None:
        sid = 200001
    else:
        sid = latest_sid.sid + 1

    if request.method == "GET":
        _rulesets = NaxsiRuleSets.query.all()
        return render_template("rules/new.html", mz=naxsi_mz, rulesets=_rulesets, score=naxsi_score, latestn=sid)

    # create new rule
    logging.debug('Posted new request: %s', request.form)
    mz = "|".join(filter(len, request.form.getlist("mz") + request.form.getlist("custom_mz_val")))

    score = request.form.get("score", "")
    score += ':'
    score += request.form.get("score_%s" % request.form.get("score", ""), "")

    nrule = NaxsiRules(request.form.get("msg", ""), request.form.get("detection", ""), mz, score, sid,
                       request.form.get("ruleset", ""), request.form.get("rmks", ""), "1",
                       request.form.get("negative", "") == 'checked', int(time()))

    nrule.validate()

    if nrule.error:
        for error in nrule.error:
            flash(error, category='error')
        return redirect(url_for("rules.new"))
    elif nrule.warnings:
        for warning in nrule.warnings:
            flash(warning, category='warnings')

    db.session.add(nrule)
    db.session.commit()

    return redirect("/rules/edit/%s" % sid)


@rules.route("/edit/<int:sid>", methods=["GET", "POST"])
def edit(sid):
    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return redirect(url_for("rules.index"))

    _rulesets = NaxsiRuleSets.query.all()
    rruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == rinfo.ruleset).first()
    custom_mz = ""
    mz_check = rinfo.mz
    if re.search(r"^\$[A-Z]+:(.*)\|[A-Z]+", mz_check):
        custom_mz = mz_check
        rinfo.mz = "custom"
    return render_template("rules/edit.html", mz=naxsi_mz, rulesets=_rulesets, score=naxsi_score, rules_info=rinfo,
                           rule_ruleset=rruleset, custom_mz=custom_mz)


@rules.route("/save/<int:sid>", methods=["POST"])
def save(sid):
    mz = "|".join(filter(len, request.form.getlist("mz") + request.form.getlist("custom_mz_val")))
    score = "{}:{}".format(request.form.get("score", ""), request.form.get("score_%s" % request.form.get("score", "")))
    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    nrule.msg = request.form.get("msg", "")
    nrule.detection = request.form.get("detection", "")
    nrule.mz = mz
    nrule.score = score
    nrule.ruleset = request.form.get("ruleset", "")
    nrule.rmks = request.form.get("rmks", "")
    nrule.active = request.form.get("active", "")
    nrule.negative = request.form.get("negative", "") == 'checked'
    nrule.timestamp = int(time())
    nrule.validate()

    if nrule.error:
        flash(",".join(nrule.error), 'error')
        return redirect("/rules/edit/%s" % sid)
    elif nrule.warnings:
        flash(",".join(nrule.warnings), 'warning')

    db.session.add(nrule)
    db.session.commit()

    return redirect("/rules/edit/%s" % sid)


@rules.route("/del/<int:sid>", methods=["GET"])
def del_sid(sid=''):
    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not nrule:
        return redirect(url_for("rules.index"))

    db.session.delete(nrule)
    db.session.commit()

    flash("Successfully deleted %s : %s" % (sid, nrule.msg), "success")
    return redirect(url_for("rules.index"))


@rules.route("/deact/<int:sid>", methods=["GET"])
def deact(sid):
    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if nrule is None:
        return redirect(url_for("rules.index"))

    fm = 'deactivate' if nrule.active else 'reactivate'
    nrule.active = not nrule.active

    db.session.add(nrule)
    db.session.commit()

    flash("Successfully deactivated %s %sd : %s" % (fm, sid, nrule.msg), "success")
    _rulesets = NaxsiRuleSets.query.all()
    return render_template("rules/edit.html", mz=naxsi_mz, rulesets=_rulesets, score=naxsi_score, rules_info=nrule)
