import logging
import re
import string
import pprint

from time import time
from flask import Blueprint, render_template, request, redirect, flash, Response, url_for
from sqlalchemy.exc import IntegrityError

from spike.model import db
from spike.model.naxsi_rules import NaxsiRules
from spike.model.naxsi_rulesets import NaxsiRuleSets
from spike.model import naxsi_mz, naxsi_score

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

    errors, warnings = nrule.validate()

    if errors:
        for error in errors:
            flash(error, category='error')
        return redirect(url_for("rules.new"))
    elif warnings:
        for warning in warnings:
            flash(warning, category='warnings')

    db.session.add(nrule)
    db.session.commit()

    return redirect("/rules/edit/%s" % sid)


@rules.route("/test/<int:sid>", methods=["GET", "POST"])
def test(sid):
    _rule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if _rule is None:
        flash("no rules found, please create one", "error")
        return redirect(url_for("rules.index"))
    return render_template("rules/test.html", rule=_rule, rtext=_rule)


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
    errors, warnings = nrule.validate()

    if errors:
        flash(",".join(errors), 'error')
        return redirect("/rules/edit/%s" % sid)
    elif warnings:
        flash(",".join(warnings), 'warning')

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


@rules.route("/import", methods=["POST", "GET"])
def import_rules():
    if request.method == "GET":
        return render_template("rules/import.html", rulesets=NaxsiRuleSets.query.all())

    ruleset = request.form.get("ruleset", "")
    upfile = request.files.get('file', '')

    if not ruleset or not upfile:
        flash("Missing rule file and/or ruleset name.", 'error')
        return redirect(url_for("rules.new"))

    raw = upfile.stream.getvalue()

    success_imports = 0
    potential_imports = 0
    for potential_rule in raw.split('\n'):
        potential_rule = potential_rule.strip()
        if not potential_rule or potential_rule.startswith("#"):  # Save ourselves some time by not trying to import comments
            continue
        potential_imports += 1
        _rule = NaxsiRules(ruleset=ruleset, active=1)
        errors, warnings, rule = _rule.parse_rule(potential_rule)
        pprint.pprint(rule)

        if errors:
            flash("Fail to parse %s: %s" % (potential_rule, ', '.join(errors)), 'error')
            continue
        else:
            db.session.add(rule)
            try:
                db.session.commit()
                success_imports += 1
            except IntegrityError:
                db.session.rollback()
                flash("Rule %s has not an unique ID" % rule['sid'])
    flash("Imported %d rules out of %d lines in ruleset %s" % (success_imports, potential_imports, ruleset))

    return render_template("rules/import.html", rulesets=NaxsiRuleSets.query.all())
