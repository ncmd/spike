import logging
import os
import re
import string
from glob import glob
from time import time, localtime, strftime

from flask import current_app, Blueprint, render_template, request, redirect, flash, Response
from sqlalchemy.exc import IntegrityError

from spike import seeds
from spike.model import *

rules = Blueprint('rules', __name__, url_prefix='/rules')


@rules.route("/")
def index():
    _rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
    if not _rules:
        flash("no rules found, please create one", "success")
        return redirect("/rules/new")
    return render_template("rules/index.html", rules=_rules)


@rules.route("/rulesets/")
def rulesets():
    return render_template("rules/rulesets.html", rulesets=NaxsiRuleSets.query.order_by(NaxsiRuleSets.name).all())


@rules.route("/rulesets/view/<path:rid>")
def ruleset_view(rid=0):
    if not rid:
        return redirect("/rulesets/")

    out_dir = current_app.config["RULES_EXPORT"]
    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access EXPORT_DIR: %s " % out_dir, "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return redirect("/rules/rulesets/")

    r = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    rf = os.path.join(out_dir, 'naxsi', r.file)
    if not os.path.isfile(rf):
        flash("ERROR while trying to read %s " % rf, "error")
        return redirect("/rules/rulesets/")

    return render_template("rules/ruleset_view.html", r=r, rout=''.join(open(rf, "r")))


@rules.route("/rulesets/new", methods=["POST"])
def ruleset_new():
    out_dir = current_app.config["RULES_EXPORT"]
    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access EXPORT_DIR: %s " % out_dir, "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return redirect("/rules/rulesets/")

    # create new rule
    rfile = request.form["rfile"].strip().lower()
    rname = request.form["rname"].strip().upper()

    cie = check_constraint("ruleset", rfile)
    if cie:
        flash("ERROR, ruleset exists: %s " % rfile, "error")
        return redirect("/rules/rulesets/")

    db.session.add(NaxsiRuleSets(rfile, rname, "naxsi-ruleset: %s" % rfile, 0, int(time())))
    try:
        db.session.commit()
        flash("OK created: %s " % rfile, "success")
    except IntegrityError:
        flash("ERROR while trying to create ruleset: %s " % rfile, "error")

    flash("OK created: %s " % rfile, "success")
    return redirect("/rules/rulesets/")


@rules.route("/rulesets/plain/<path:rid>")
def ruleset_plain(rid=0):
    """
    Show the rule `rid` in plain text
    :param int rid: Rule id
    """
    if not rid:
        return redirect("/rulesets/")
    out_dir = current_app.config["RULES_EXPORT"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access EXPORT_DIR: %s " % out_dir, "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return redirect("/rules/rulesets/")

    r = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    rf = "%s/naxsi/%s" % (out_dir, r.file)
    if not os.path.isfile(rf):
        flash("ERROR while trying to read %s " % rf, "error")
        return redirect("/rules/rulesets/")

    return Response("".join(open(rf, "r")), mimetype='text/plain')


@rules.route("/select/<path:selector>", methods=["GET"])
def nx_select(selector=''):
    if not selector:
        return redirect("/rules/")

    sel = str(selector)
    logging.info("sel: %s ", sel)
    try:
        rs_val = sel.split(":")[1]
    except:
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

    try:
        nrule = NaxsiRules(request.form["msg"], detect, mz, score, sid, ruleset, rmks, "1", negative, int(time()))
        db.session.add(nrule)
        db.session.commit()
        flash("OK: created %s : %s" % (sid, request.form["msg"]), "success")
        return redirect("/rules/edit/%s" % sid)
    except:
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
    nruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == nrule.ruleset).first()
    nruleset.updated = 1
    db.session.add(nruleset)
    try:
        db.session.commit()
        flash("OK: updated %s : %s" % (sid, msg), "success")
    except:
        flash("ERROR while trying to update %s : %s" % (sid, msg), "error")
    return redirect("/rules/edit/%s" % sid)


@rules.route("/view/<path:sid>", methods=["GET"])
def view(sid=''):
    if not sid:
        return redirect("/rules/")

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return redirect("/rules/")

    return render_template("rules/view.html", rule=rinfo, rtext=z_display_rule(rinfo, full=0))


@rules.route("/del/<path:sid>", methods=["GET"])
def del_sid(sid=''):
    if not sid:
        return redirect("/rules/")

    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not nrule:
        return redirect("/rules/")

    nruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == nrule.ruleset).first()
    nruleset.updated = 1
    db.session.add(nruleset)
    db.session.delete(nrule)
    try:
        db.session.commit()
        flash("OK: deleted %s : %s" % (sid, nrule.msg), "success")
    except:
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
    except:
        flash("ERROR while trying to %s %s : %s" % (fm, sid, nrule.msg), "error")

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return redirect("/rules/")

    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
    score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
    _rulesets = NaxsiRuleSets.query.all()
    return render_template("rules/edit.html", mz=mz, rulesets=_rulesets, score=score, rules_info=rinfo)


@rules.route("/export/", methods=["GET"])
@rules.route("/export/<path:rid>", methods=["GET"])
def export_ruleset(rid='all'):
    out_dir = current_app.config["RULES_EXPORT"]
    naxsi_out = "%s/naxsi" % out_dir
    export_date = strftime("%F - %H:%M", localtime(time()))

    if rid == "all":
        rsets = NaxsiRuleSets.query.filter(NaxsiRuleSets.updated != 0).all()
    else:
        rsets = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).all()

    if not rsets:
        flash("Nothing to export, no rules changed", "success")
        return redirect("/rules/rulesets/")

    # naxsi-exports
    for rs in rsets:
        of = "%s/%s" % (naxsi_out, rs.file)
        logging.info("exporting %s", of)
        try:
            f = open(of, "w")
            head = current_app.config["RULESET_HEADER"].replace("RULESET_DESC", rs.name).replace("RULESET_FILE",
                                                                                                 rs.file).replace(
                "RULESET_DATE", export_date)
            f.write(head)
        except:
            flash("ERROR while trying to export %s" % rs.file, "error")
            return redirect("/rules/")
        _rules = NaxsiRules.query.filter(NaxsiRules.ruleset == rs.file, NaxsiRules.active == 1).order_by(
            NaxsiRules.sid.desc()).all()
        nxruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == rs.file).first()
        nxruleset.updated = 0
        db.session.add(nxruleset)
        db.session.commit()
        for rule in _rules:
            rout = z_display_rule(rule)
            f.write("%s \n" % rout)
        f.close()
        flash("Exported: %s / %s" % (rid, of), "success")

    return redirect("/rules/rulesets/")


@rules.route("/import/", methods=["GET", "POST"])
def import_ruleset():
    out_dir = current_app.config["RULES_EXPORT"]
    import_date = strftime("%F - %H:%M", localtime(time()))

    if request.method == "GET":
        return render_template("rules/import.html", rulesets=NaxsiRuleSets.query.all())

    # create new rule
    ts = int(time())
    nr = request.form
    rset = nr["ruleset"].strip().lower()
    rcust = nr["cruleset"].strip().lower()

    if len(rcust) > 4:
        rset = rcust
        flash("creating new ruleset for import: %s" % rcust, "success")
        rname = rset.split(".")[0].upper()
        rnew = NaxsiRuleSets(rset, rname, "naxsi-ruleset: %s" % rcust, ts, ts)
        db.session.add(rnew)
        db.session.commit()
        flash("OK created: %s " % rset, "success")

    for r in nr["rules"].split("\n"):
        r = r.strip()
        if len(r) < 30 or r.startswith("#") or not r.startswith("MainRule"):
            continue

        flash("importing: %s" % r, "success")
        msg = detect = mz = score = sid = 0
        rs = r.split("\"")
        logging.debug('%s', rs)
        rmks = "imported: %s / %s" % (rset, strftime("%Y - %H:%M", localtime(float(ts))))
        for sr in rs:
            # stripping leading/ending maskings "
            sr = sr.strip()
            if sr == "MainRule":
                continue
            try:
                z = sr.split(":")
            except:
                continue

            if len(z) < 2:
                continue
            if z[0] == "msg":
                msg = ":".join(z[1:])
            elif z[0] == "str":
                detect = "str:%s" % ":".join(z[1:])
            elif z[0] == "rx":
                detect = "rx:%s" % ":".join(z[1:])
            elif z[0] == "s":
                score = ":".join(z[1:])
            elif z[0] == "mz":
                mz = ":".join(z[1:])
            elif z[0] == "id":
                sid = z[1].replace(";", "").strip()

        if NaxsiRules.query.filter(NaxsiRules.sid == sid).first():
            old_sid = sid
            sid = check_or_get_latest_sid(sid)
            flash("changing sid: orig: %s / new: %s" % (old_sid, sid), "success")
            rmks = "%s \nchanged sid: orig: %s / new: %s " % (rmks, old_sid, sid)

        nrule = NaxsiRules(msg, detect, mz, score, sid, rset, rmks, "1", ts, ts)
        db.session.add(nrule)
        db.session.commit()
        flash("OK: created %s : %s" % (sid, msg), "success")

    return redirect("/rules/export/")


@rules.route("/backup/", methods=["GET"])
def rules_backup_view(action="show"):
    out_dir = current_app.config["BACKUP_DIR"]
    sqlite_bin = current_app.config["SQLITE_BIN"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access BACKUP_DIR: %s " % out_dir, "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return redirect("/rules/")

    bfiles = {}
    bfiles_in = glob("%s/*.sql.*" % out_dir)
    logging.debug('%s', bfiles_in)
    for b in bfiles_in:
        bx = b.split("/")
        logging.debug(bx)
        bname = bx[-1]
        bid = bx[-1].split(".")[-1]
        bdate = strftime("%F - %H:%M", localtime(float(bx[-1].split(".")[-1])))  # extension is nb sec since epoch
        bfiles[bid] = [bname, bdate]

    return render_template("rules/backups.html", bfiles=bfiles)


@rules.route("/backup/<path:action>", methods=["GET"])
def rules_backup(action="show"):  # FIXME this is full of duplicate code :/
    out_dir = current_app.config["BACKUP_DIR"]
    sqlite_bin = current_app.config["SQLITE_BIN"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access BACKUP_DIR: %s " % out_dir, "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return redirect("/rules/")

    if action == "create":
        bdate = int(time())
        bfile = "%s/rules.sql.%s" % (out_dir, bdate)
        rules_db = "spike/rules.db"
        if not os.path.isfile(sqlite_bin) or not os.access(sqlite_bin, os.X_OK):
            flash("ERROR, no sqlite_bin found in: %s " % sqlite_bin, "error")
            flash("you might want to adjust your <a href=\"/settings\">Settings</a> and install sqlite", "error")
            return redirect("/rules/backup")

        with open(bfile, "w") as f:
            f.write("-- spike-dump %s \n\n" % strftime("%F - %H:%M", localtime(float(bdate))))

        try:
            os.system("%s %s  .dump >> %s" % (sqlite_bin, rules_db, bfile))
            flash("creating backup %s" % bdate, "success")
            flash("backup OK in %s" % bfile, "success")
        except:
            flash("ERRORwhile executing dump %s " % bfile, "error")

    elif action == "show":
        bfiles = {}
        bfiles_in = glob("%s/*.sql.*" % out_dir)
        logging.debug(bfiles_in)
        for b in bfiles_in:  # this is duplicate
            bx = b.split("/")
            logging.debug('%s', bx)
            bname = bx[-1]
            bid = bx[-1].split(".")[-1]
            bdate = strftime("%F - %H:%M", localtime(float(bx[-1].split(".")[-1])))
            bfiles[bid] = [bname, bdate]

        return render_template("rules/backups.html", bfiles=bfiles)

    elif action == "reload":
        try:
            bid = request.args.get('bid')
        except:
            flash("ERROR, no backup - id selected ", "error")
            return redirect("/rules/backup")

        bfile = "%s/rules.sql.%s" % (out_dir, bid)
        rules_db = "spike/rules.db"

        if not os.path.isfile(sqlite_bin) or not os.access(sqlite_bin, os.X_OK):
            flash("ERROR, no sqlite_bin found in: %s " % sqlite_bin, "error")
            flash("you might want to adjust your <a href=\"/settings\">Settings</a> and install sqlite", "error")
            return redirect("/rules/backup")

        try:
            os.unlink(rules_db)
            os.system("%s %s < %s" % (sqlite_bin, rules_db, bfile))
            flash("restored db.backup < %s" % bfile, "success")
        except:
            flash("ERROR while executing dump %s " % bfile, "error")
    elif action == "display":
        try:
            bid = request.args.get('bid')
        except:
            flash("ERROR, no backup - id selected ", "error")
            return redirect("/rules/backup")

        if not os.path.isfile("%s/rules.sql.%s" % (out_dir, bid)):
            flash("ERROR, no backup found for id: %s" % bid, "error")
            return redirect("/rules/backup")

        return Response("".join(open("%s/rules.sql.%s" % (out_dir, bid), "r").readlines()), mimetype='text/plain')

    elif action == "delete":
        try:
            bid = request.args.get('bid')
        except:
            flash("ERROR, no backup - id selected ", "error")
            return redirect("/rules/backup")

        if not os.path.isfile("%s/rules.sql.%s" % (out_dir, bid)):
            flash("ERROR, no backup found for id: %s" % bid, "error")
            return redirect("/rules/backup")

        os.unlink("%s/rules.sql.%s" % (out_dir, bid))
        flash("backup deleted: %s/rules.sql.%s" % (out_dir, bid), "success")
    else:
        flash("ERROR, no backup - action selected ", "error")

    return redirect("/rules/backup")


def z_display_rule(rule, full=1):
    rdate = strftime("%F - %H:%M", localtime(float(str(rule.timestamp))))
    rmks = "# ".join(rule.rmks.strip().split("\n"))
    detect = rule.detection.lower() if rule.detection.startswith("str:") else rule.detection
    negate = 'negative' if rule.negative == 1 else ''

    if full == 1:
        nout = """#
# sid: %s | date: %s 
#
# %s
#
MainRule %s "%s" "msg:%s" "mz:%s" "s:%s" id:%s  ;
      
      """ % (rule.sid, rdate, rmks, negate, detect, rule.msg, rule.mz, rule.score, rule.sid)
    else:
        nout = """MainRule %s "%s" "msg:%s" "mz:%s" "s:%s" id:%s  ;""" % \
               (negate, rule.detection, rule.msg, rule.mz, rule.score, rule.sid)

    return nout
