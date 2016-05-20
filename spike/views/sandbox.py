try:
    from urlparse import parse_qs
except ImportError:  # python3
    from urllib.parse import parse_qs

from flask import Blueprint, render_template, request, redirect, flash, url_for

from nxapi import nxlog

from spike.model.naxsi_rules import NaxsiRules
from spike.model.naxsi_whitelist import NaxsiWhitelist

sandbox = Blueprint('sandbox', __name__)


@sandbox.route("/", methods=["GET"])
def index():
    return render_template("misc/sandbox.html")


@sandbox.route("/explain_rule/", methods=["GET", "POST"])
def explain_rule():
    errors = warnings = list()
    rule_get = request.args.get('rule', '')
    rule_post = request.form.get("rule", '')
    if rule_get.isdigit():  # explain a rule by id
        _rule = NaxsiRules.query.filter(NaxsiRules.sid == rule_get).first()
        if _rule is None:
            flash('Not rule with id %s' % rule_get)
            return redirect(url_for("sandbox.index"))
    elif rule_get is not '':
        flash('Please provide a numeric id')
        return redirect(url_for("sandbox.index"))
    elif not rule_post:
        flash('Please provide a rule')
        return redirect(url_for("sandbox.index"))
    else:
        _rule = NaxsiRules()
        errors, warnings, rdict = _rule.parse_rule(rule_post)
        _rule = NaxsiRules()
        _rule.from_dict(rdict)
        _rule.errors = errors
        _rule.warnings = warnings

        if _rule.errors:
            flash('You rule is wrong', 'error')
            return render_template("misc/sandbox.html")

    if 'visualise_rule' in request.form:
        if _rule.detection.startswith('rx:'):
            return redirect('https://regexper.com/#' + _rule.detection[3:])
        else:
            flash('The rule is not a regexp, so you can not visualize it.', category='error')

    if errors:
        for error in errors:
            flash(error, category='error')
    if warnings:
        for warnings in warnings:
            flash(warnings, category='warning')

    return render_template("misc/sandbox.html", rule_explaination=_rule.explain(), rule=_rule)


@sandbox.route("/explain_whitelist/", methods=["GET", "POST"])
def explain_whitelist():
    whitelist_get = request.args.get('whitelist', '')
    whitelist_post = request.form.get('whitelist', '')
    if whitelist_get.isdigit():  # explain a whitelist by id
        _wl = NaxsiWhitelist.query.filter(NaxsiWhitelist.id == whitelist_get).first()
        if _wl is None:
            flash('Not rule with id %s' % whitelist_get)
            return redirect(url_for("sandbox.index"))
    elif whitelist_get is not '':
        flash('Please provide a numeric id')
        return redirect(url_for("sandbox.index"))
    elif not whitelist_post:
        flash('Please provide a whitelist')
        return redirect(url_for("sandbox.index"))
    else:
        _wl = NaxsiWhitelist()
        errors, warnings, rdict = _wl.parse(whitelist_post)
        _wl = NaxsiWhitelist()
        _wl.from_dict(rdict)
        _wl.errors = errors
        _wl.warnings = warnings

    if _wl.errors:
        for error in _wl.errors:
            flash(error, category='error')
    if _wl.warnings:
        for warnings in _wl.warnings:
            flash(warnings, category='warning')

    return render_template("misc/sandbox.html", whitelist_explaination=_wl.explain(), whitelist=_wl)


@sandbox.route('/explain_nxlog/', methods=["POST"])
def explain_nxlog():
    _nxlog = request.form.get("nxlog", '')
    if not _nxlog:
        return redirect(url_for("sandbox.index"))

    errors, nxdic = nxlog.parse_nxlog(_nxlog)
    if errors:
        flash(''.join(errors))
        return redirect(url_for("sandbox.index"))

    return render_template("misc/sandbox.html", nxlog_explaination=nxlog.explain_nxlog(nxdic), nxlog=_nxlog)
