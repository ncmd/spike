import logging
import re
import string
from time import time, localtime, strftime

from flask import current_app, Blueprint, render_template, request, redirect, flash, Response
from sqlalchemy.exc import SQLAlchemyError

from spike.model import NaxsiRules, NaxsiRuleSets
from spike.model import check_constraint, db, check_or_get_latest_sid
from spike.model.naxsi_rules import ValueTemplates

rules = Blueprint('rules', __name__, url_prefix='/rules')

# TODO : merge `ruleset_plain` and `ruleset_view`


@rules.route("/")
def index():
    _rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
    if not _rules:
        flash("no rules found, please create one", "success")
        return redirect("/rules/new")
    return render_template("rules/index.html", rules=_rules)

@rules.route("/plain/<int:sid>")
def rule_plain(sid):
    sid = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    return Response(__get_textual_representation_rule(sid), mimetype='text/plain')


@rules.route("/rulesets/")
def rulesets():
    _rulesets = NaxsiRuleSets.query.order_by(NaxsiRuleSets.name).all()
    return render_template("rules/rulesets.html", rulesets=_rulesets)


def __get_rules_for_ruleset(ruleset, with_header = True):

    _rules = NaxsiRules.query.filter(
        NaxsiRules.ruleset == ruleset.file,
        NaxsiRules.active == 1
    ).all()

    nxruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == ruleset.file).first()
    db.session.add(nxruleset)
    db.session.commit()
    text_rules = ''.join(map(__get_textual_representation_rule, _rules))

    if with_header is False:
        return text_rules

    header = current_app.config["RULESET_HEADER"]
    header = header.replace("RULESET_DESC", ruleset.name)
    header = header.replace("RULESET_FILE", ruleset.file)
    header = header.replace( "RULESET_DATE", strftime("%F - %H:%M", localtime(time())))

    return header + text_rules


@rules.route("/rulesets/plain/")
@rules.route("/rulesets/plain/<int:rid>")
def ruleset_plain(rid=0):
    """
    Show the rule `rid` in plain text
    :param int rid: Rule id
    """
    if not rid:
        out = ''.join(map(__get_rules_for_ruleset, NaxsiRuleSets.query.all()))
    else:
        out = __get_rules_for_ruleset(NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first())
    return Response(out, mimetype='text/plain')


@rules.route("/rulesets/view/<int:rid>")
def ruleset_view(rid=0):
    if not rid:
        return redirect("/rulesets/")
    ruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    return render_template("rules/ruleset_view.html", r=ruleset, rout=__get_rules_for_ruleset(ruleset))

@rules.route("/rulesets/new", methods=["POST"])
def ruleset_new():  # TODO filter parameter
    rfile = request.form["rfile"].strip().lower()
    rname = request.form["rname"].strip().upper()

    cie = check_constraint("ruleset", rfile)
    if cie:
        flash("ERROR, ruleset exists: %s " % rfile, "error")
        return redirect("/rules/rulesets/")

    db.session.add(NaxsiRuleSets(rfile, rname, "naxsi-ruleset: %s" % rfile, int(time())))
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("ERROR while trying to create ruleset: %s " % rfile, "error")

    flash("OK created: %s " % rfile, "success")
    return redirect("/rules/rulesets/")


@rules.route("/select/<path:selector>", methods=["GET"])
def nx_select(selector=''):
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
    sid = check_or_get_latest_sid()

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


@rules.route("/view/<path:sid>", methods=["GET"])
def view(sid=''):
    if not sid:
        return redirect("/rules/")

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return redirect("/rules/")

    return render_template("rules/view.html", rule=rinfo, rtext=__get_textual_representation_rule(rinfo, full=0))


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
def deact_sid(sid=''):
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
