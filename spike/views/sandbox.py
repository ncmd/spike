try:
    from urlparse import parse_qs
except ImportError:  # python3
    from urllib.parse import parse_qs

from flask import Blueprint, render_template, request, redirect, flash, url_for

from spike.model.naxsi_rules import NaxsiRules
from spike.model.naxsi_whitelist import NaxsiWhitelist

sandbox = Blueprint('sandbox', __name__)


@sandbox.route("/", methods=["GET"])
def index():
    return render_template("misc/sandbox.html")


@sandbox.route("/explain_rule/", methods=["GET", "POST"])
def explain_rule():
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
        _rule.parse_rule(rule_post)

    if 'visualise_rule' in request.form:
        if _rule.detection.startswith('rx:'):
            return redirect('https://regexper.com/#' + _rule.detection[3:])
        else:
            flash('The rule is not a regexp, so you can not visualize it.', category='error')

    if hasattr(_rule, 'error'):
        for error in _rule.error:
            flash(error, category='error')
    if hasattr(_rule, 'warning'):
        for warnings in _rule.warnings:
            flash(warnings, category='warning')

    return render_template("misc/sandbox.html", rule_explaination=_rule.explain(), rule=_rule)


@sandbox.route("/explain_whitelist/", methods=["GET", "POST"])
def explain_whitelist():
    whitelist_get = request.args.get('whitelist', '')
    whitelist_post = request.form.get('whitelist', '')
    if whitelist_get.isdigit():  # explain a whitelist by id
        _wlist = NaxsiWhitelist.query.filter(NaxsiWhitelist.id == whitelist_get).first()
        if _wlist is None:
            flash('Not rule with id %s' % whitelist_get.id)
            return redirect(url_for("sandbox.index"))
    elif whitelist_get is not '':
        flash('Please provide a numeric id')
        return redirect(url_for("sandbox.index"))
    elif not whitelist_post:
        flash('Please provide a whitelist')
        return redirect(url_for("sandbox.index"))
    else:
        _wlist = NaxsiWhitelist()
        _wlist.parse(whitelist_post)

    if hasattr(_wlist, 'error'):
        for error in _wlist.error:
            flash(error, category='error')
    if hasattr(_wlist, 'warning'):
        for warnings in _wlist.warnings:
            flash(warnings, category='warning')

    return render_template("misc/sandbox.html", whitelist_explaination=_wlist.explain(), whitelist=_wlist)


@sandbox.route('/explain_nxlog/', methods=["POST"])
def explain_nxlog():
    nxlog = request.form.get("nxlog", '')
    if not nxlog:
        return redirect(url_for("sandbox.index"))

    start = nxlog.find("ip=")
    if start < 0:
        flash('{} is an invalid extlog, string "ip=" not found.'.format(nxlog))
        return redirect(url_for("sandbox.index"))

    end = nxlog.find(", ")
    if end < 0:
        flash('{} is an invalid extlog, string "," not found.'.format(nxlog))
        return redirect(url_for("sandbox.index"))

    # Flatten the dict, since parse_qs is a bit annoying
    nxdic = parse_qs(nxlog[start:end])
    for key, value in nxdic.items():
        nxdic[key] = value[0]

    explain = "Peer <strong>{}</strong> performed a request to <strong>{}</strong> on URI <strong>{}</strong> ".format(
        nxdic['ip'], nxdic['server'], nxdic['uri'])

    scores = list()
    cpt = 0
    while "cscore{}".format(cpt) in nxdic:
        cscore = "cscore{}".format(cpt)
        score = "score{}".format(cpt)
        scores.append("that reached a <strong>{}</strong> score of <strong>{}</strong> ".format(
            nxdic[cscore], nxdic[score]))
        cpt += 1
    explain += ' and '.join(scores)

    cpt = 0
    named = list()
    while "id{}".format(cpt) in nxdic:
        _id = "id{}".format(cpt)
        _var_name = "var_name{}".format(cpt)
        _zone = "zone{}".format(cpt)
        if "var_name{}".format(cpt) in nxdic:
            named.append("id <strong>{}</strong> in var named <strong>{}</strong> of zone <strong>{}</strong>".format(
                nxdic[_id], nxdic[_var_name], nxdic[_zone]))
        else:
            named.append("id <strong>{}</strong> in zone <strong>{}</strong>".format(nxdic[_id], nxdic[_zone]))
        cpt += 1
    explain += ' and '.join(named)

    return render_template("misc/sandbox.html", nxlog_explaination=explain, nxlog=nxlog)
