import logging
import re
import string
from time import time, localtime, strftime

from flask import Blueprint, render_template, request, redirect, flash, Response
from sqlalchemy.exc import SQLAlchemyError

from spike.model import db
from spike.model.naxsi_rules import NaxsiRules
from spike.model.value_templates import ValueTemplates
from spike.model.naxsi_rulesets import NaxsiRuleSets

rules = Blueprint('rules', __name__)


@rules.route("/")
def index():
    _rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
    if not _rules:
        flash("no rules found, please create one", "success")
        return redirect("/rules/new")
    return render_template("rules/index.html", rules=_rules)


@rules.route("/plain/<int:sid>", methods=["GET"])
def plain(sid):
    _rule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not _rule:
        flash("no rules found, please create one", "error")
        return redirect("/rules/new")

    return Response(__get_textual_representation_rule(_rule), mimetype='text/plain')


@rules.route("/view/<path:sid>", methods=["GET"])
def view(sid=''):
    _rule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not _rule:
        flash("no rules found, please create one", "error")
        return redirect("/rules/")

    return render_template("rules/view.html", rule=_rule, rtext=__get_textual_representation_rule(_rule, full=0))


@rules.route("/select/<path:selector>", methods=["GET"])
def select(selector=''):
    if not selector:
        return redirect("/rules/")

    sel = str(selector)
    logging.info("sel: %s ", sel)
    try:
        rs_val = sel.split(":")[1]
    except SQLAlchemyError:
        return redirect("/rules/")

    if sel.startswith('r:'):
        _rules = NaxsiRules.query.filter(NaxsiRules.ruleset == rs_val).order_by(NaxsiRules.sid.desc()).all()
        selection = "Search ruleset: %s " % rs_val
    elif sel.startswith('id:'):
        _rules = NaxsiRules.query.filter(NaxsiRules.sid == rs_val).order_by(NaxsiRules.sid.desc()).all()
        selection = "Search sid: %s " % rs_val
    else:
        return redirect("/rules/")

    return render_template("rules/index.html", rules=_rules, selection=selection)


@rules.route("/search/", methods=["GET"])
def search():
    terms = request.args.get('s', '')

    if len(terms) < 2:
        return redirect('/rules')

    # No fancy injections
    whitelist = set(string.ascii_letters + string.digits + ':-_ ')
    filtered = ''.join(filter(whitelist.__contains__, terms))

    if filtered.isdigit():  # get rule by id
        _rules = db.session.query(NaxsiRules).filter(NaxsiRules.sid == int(filtered)).all()
    else:
        expression = '%' + filtered + '%'
        _rules = db.session.query(NaxsiRules).filter(
            db.or_(
                NaxsiRules.msg.like(expression),
                NaxsiRules.rmks.like(expression),
                NaxsiRules.detection.like(expression)
            )
        ).order_by(NaxsiRules.sid.desc()).all()
    return render_template("rules/index.html", rules=_rules, selection="Search: %s" % filtered, lsearch=terms)


@rules.route("/new", methods=["GET", "POST"])
def new():
    latest_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
    if latest_sid is None:
        sid = 200001
    else:
        sid = latest_sid.sid + 1

    if request.method == "GET":
        mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
        _rulesets = NaxsiRuleSets.query.all()
        score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
        return render_template("rules/new.html", mz=mz, rulesets=_rulesets, score=score, latestn=sid)

    # create new rule
    logging.debug('Posted new request: %s', request.form)

    detect = str(request.form["detection"]).strip()
    if not detect.startswith("str:") and not detect.startswith("rx:"):
        detect = "str:%s" % detect

    mz = "|".join(request.form.getlist("mz"))

    try:
        if request.form["custom_mz"] == "on":
            mz = "%s|%s" % (mz, request.form["custom_mz_val"])
    except:
        pass

    score_raw = request.form["score"].strip()
    score_val = request.form["score_%s" % score_raw].strip()
    score = "%s:%s" % (score_raw, score_val)
    rmks = request.form["rmks"]
    ruleset = request.form["ruleset"]
    negative = 'negative' in request.form and request.form['negative'] == 'checked'

    nrule = NaxsiRules(request.form["msg"], detect, mz, score, sid, ruleset, rmks, "1", negative, int(time()))
    db.session.add(nrule)

    try:
        db.session.commit()
        flash("OK: created %s : %s" % (sid, request.form["msg"]), "success")
        return redirect("/rules/edit/%s" % sid)
    except SQLAlchemyError:
        flash("ERROR while trying to create %s : %s" % (sid, request.form["msg"]), "error")

    return redirect("/rules/new")


@rules.route("/edit/<path:sid>", methods=["GET", "POST"])
def edit(sid=''):
    if not sid:
        return redirect("/rules/")

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return redirect("/rules/")

    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
    score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
    _rulesets = NaxsiRuleSets.query.all()
    rruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == rinfo.ruleset).first()
    custom_mz = ""
    mz_check = rinfo.mz
    if re.search(r"^\$[A-Z]+:(.*)\|[A-Z]+", mz_check):
        custom_mz = mz_check
        rinfo.mz = "custom"
    return render_template("rules/edit.html", mz=mz, rulesets=_rulesets, score=score, rules_info=rinfo,
                           rule_ruleset=rruleset, custom_mz=custom_mz)


@rules.route("/save/<path:sid>", methods=["POST"])
def save(sid=''):  # FIXME this is the exact same method as the `new` one.
    if not sid:
        return redirect("/rules/")

    # create new rule
    try:
        msg = request.form["msg"]
        detect = str(request.form["detection"]).strip()
        if not detect.startswith("str:") and not detect.startswith("rx:"):
            detect = "str:%s" % detect
        mz = "|".join(request.form.getlist("mz"))
        try:
            if request.form["custom_mz"] == "on":
                if len(mz) > 1:
                    mz = "%s|%s" % (request.form["custom_mz_val"], mz)
                else:
                    mz = "%s" % (request.form["custom_mz_val"])
        except:
            pass
        score_raw = request.form["score"].strip()
        score_val = request.form["score_%s" % score_raw].strip()
        score = "%s:%s" % (score_raw, score_val)
        # sid = nr["sid"]
        rmks = request.form["rmks"]
        ruleset = request.form["ruleset"]
        active = request.form["active"]
        negative = 'negative' in request.form and request.form['negative'] == 'checked'
    except:
        flash('ERROR - please select MZ/Score <a href="javascript:alert(history.back)">Go Back</a>', "error")
        return redirect("/rules/edit/%s" % sid)

    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    nrule.msg = msg
    nrule.detection = detect
    nrule.mz = mz
    nrule.score = score
    nrule.ruleset = ruleset
    nrule.rmks = rmks
    nrule.active = active
    nrule.negative = negative
    nrule.timestamp = int(time())
    db.session.add(nrule)
    try:
        db.session.commit()
    except SQLAlchemyError:
        flash("ERROR while trying to update %s : %s" % (sid, msg), "error")
    return redirect("/rules/edit/%s" % sid)


@rules.route("/del/<path:sid>", methods=["GET"])
def del_sid(sid=''):
    if not sid:
        return redirect("/rules/")

    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not nrule:
        return redirect("/rules/")

    db.session.delete(nrule)
    try:
        db.session.commit()
        flash("OK: deleted %s : %s" % (sid, nrule.msg), "success")
    except SQLAlchemyError:
        flash("ERROR while trying to update %s : %s" % (sid, nrule.msg), "error")

    return redirect("/rules/")


@rules.route("/deact/<path:sid>", methods=["GET"])
def deact(sid=''):
    if not sid:
        return redirect("/rules/")

    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not nrule:
        return redirect("/rules/")

    if nrule.active == 0:
        nrule.active = 1
        fm = "reactivate"
    else:
        nrule.active = 0
        fm = "deactivate"

    db.session.add(nrule)
    try:
        db.session.commit()
        flash("OK: %s %sd : %s" % (fm, sid, nrule.msg), "success")
    except SQLAlchemyError:
        flash("ERROR while trying to %s %s : %s" % (fm, sid, nrule.msg), "error")

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return redirect("/rules/")

    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
    score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
    _rulesets = NaxsiRuleSets.query.all()
    return render_template("rules/edit.html", mz=mz, rulesets=_rulesets, score=score, rules_info=rinfo)


def __get_textual_representation_rule(rule, full=1):
    rdate = strftime("%F - %H:%M", localtime(float(str(rule.timestamp))))
    rmks = "# ".join(rule.rmks.strip().split("\n"))
    detect = rule.detection.lower() if rule.detection.startswith("str:") else rule.detection
    negate = 'negative' if rule.negative == 1 else ''

    if full == 1:
        nout = """
#
# sid: %s | date: %s
#
# %s
#
MainRule %s "%s" "msg:%s" "mz:%s" "s:%s" id:%s ;

""" % (rule.sid, rdate, rmks, negate, detect, rule.msg, rule.mz, rule.score, rule.sid)
    else:
        nout = """MainRule %s "%s" "msg:%s" "mz:%s" "s:%s" id:%s  ;""" % \
               (negate, rule.detection, rule.msg, rule.mz, rule.score, rule.sid)

    return nout
