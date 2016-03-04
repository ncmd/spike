from flask import current_app, Blueprint, render_template, request, redirect, flash, Response
from spike.model import NaxsiRules, NaxsiRuleSets
from time import time, localtime, strftime
from spike.model import check_constraint, db
from sqlalchemy.exc import SQLAlchemyError

from rules import __get_textual_representation_rule

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
def view(rid=0):
    if not rid:
        return redirect("/rulesets/")
    ruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    return render_template("/rulesets/view.html", r=ruleset, rout=__get_rules_for_ruleset(ruleset))


@rulesets.route("/new", methods=["POST"])
def new():  # TODO filter parameter
    rfile = request.form["rfile"].strip().lower()
    rname = request.form["rname"].strip().upper()

    cie = check_constraint("ruleset", rfile)
    if cie:
        flash("ERROR, ruleset exists: %s " % rfile, "error")
        return redirect("/rulesets/")

    db.session.add(NaxsiRuleSets(rfile, rname, "naxsi-ruleset: %s" % rfile, int(time())))
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("ERROR while trying to create ruleset: %s " % rfile, "error")

    flash("OK created: %s " % rfile, "success")
    return redirect("/rulesets/")


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
