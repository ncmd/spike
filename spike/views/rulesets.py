from time import time, localtime, strftime

from flask import current_app, Blueprint, render_template, request, redirect, flash, Response

from spike.model import db
from spike.model.naxsi_rules import NaxsiRules
from spike.model.naxsi_rulesets import NaxsiRuleSets


rulesets = Blueprint('rulesets', __name__)


@rulesets.route("/")
def index():
    _rulesets = NaxsiRuleSets.query.order_by(NaxsiRuleSets.name).all()
    return render_template("/rulesets/index.html", rulesets=_rulesets)


@rulesets.route("/plain/")
@rulesets.route("/plain/<int:rid>")
def plain(rid=0):
    """
    Show the rule `rid` in plain text
    :param int rid: Rule id
    """
    if not rid:
        out = ''.join(map(__get_rules_for_ruleset, NaxsiRuleSets.query.all()))
    else:
        out = __get_rules_for_ruleset(NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first())
    return Response(out, mimetype='text/plain')


@rulesets.route("/view/<int:rid>")
def view(rid):
    ruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    return render_template("/rulesets/view.html", r=ruleset, rout=__get_rules_for_ruleset(ruleset))


@rulesets.route("/new", methods=["POST"])
def new():  # TODO filter parameter
    rname = request.form["rname"].strip().upper()

    if NaxsiRuleSets.query.filter(NaxsiRuleSets.name == rname).first():
        flash("ERROR, ruleset exists: %s " % rname, "error")
        return redirect("/rulesets/")

    db.session.add(NaxsiRuleSets(rname, "naxsi-ruleset: %s" % rname, int(time())))
    db.session.commit()

    flash("OK created: %s " % rname, "success")
    return redirect("/rulesets/")


@rulesets.route("/del/<int:rname>", methods=["POST"])
def remove(rname):
    _rset = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rname).first()
    if _rset is None:
        flash("ERROR, ruleset doesn't exists: %s " % rname, "error")
        return redirect("/rulesets/")

    db.session.delete(_rset)
    db.session.commit()

    flash("OK deleted: %s " % rname, "success")
    return redirect("/rulesets/")


@rulesets.route("/select/<string:selector>", methods=["GET"])
def select(selector):
    _rules = NaxsiRules.query.filter(NaxsiRules.ruleset == selector).order_by(NaxsiRules.sid.desc()).all()
    _selection = "Search sid: %s " % selector
    return render_template("rules/index.html", rules=_rules, selection=_selection)


def __get_rules_for_ruleset(ruleset):
    if not ruleset:
        return ''

    _rules = NaxsiRules.query.filter(
        NaxsiRules.ruleset == ruleset.name,
        NaxsiRules.active == 1
    ).all()

    nxruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == ruleset.name).first()
    db.session.add(nxruleset)
    db.session.commit()

    text_rules = ''.join([r.fullstr() for r in _rules])

    header = current_app.config["RULESET_HEADER"]
    header = header.replace("RULESET_DESC", ruleset.name)
    header = header.replace("RULESET_DATE", strftime("%F - %H:%M", localtime(time())))

    return header + text_rules
