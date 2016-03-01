import os
import re
from glob import glob
from time import time, localtime, strftime

from flask import current_app, Blueprint, render_template, request, redirect, flash, Response

from spike import seeds
from spike.model import *
from spike.views import demo_mode

rules = Blueprint('rules', __name__, url_prefix='/rules')


@rules.route("/")
def index():
    rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
    if not rules:
        flash("no rules found, please create one", "success")
        return (redirect("/rules/new"))

    return (render_template("rules/index.html", rules=rules))


@rules.route("/rulesets/")
def rulesets():
    rulesets = NaxsiRuleSets.query.order_by(NaxsiRuleSets.name).all()
    return (render_template("rules/rulesets.html", rulesets=rulesets))


@rules.route("/rulesets/view/<path:rid>")
def ruleset_view(rid=0):
    if rid == 0:
        return (redirect("/rulesets/"))
    r = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    out_dir = current_app.config["RULES_EXPORT"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access EXPORT_DIR: %s " % (out_dir), "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return (redirect("/rules/rulesets/"))

    rf = "%s/naxsi/%s" % (out_dir, r.file)
    if not os.path.isfile(rf):
        flash("ERROR while trying to read %s " % (rf), "error")
        return (redirect("/rules/rulesets/"))

    rout = "".join(open(rf, "r"))

    return (render_template("rules/ruleset_view.html", r=r, rout=rout))


@demo_mode("")
@rules.route("/rulesets/new", methods=["POST"])
def ruleset_new():
    out_dir = current_app.config["RULES_EXPORT"]
    from sqlalchemy.exc import IntegrityError
    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access EXPORT_DIR: %s " % (out_dir), "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return (redirect("/rules/rulesets/"))

    if request.method == "POST":
        # create new rule
        ts = int(time())
        nr = request.form
        rfile = nr["rfile"].strip().lower()
        rname = nr["rname"].strip().upper()
        cie = check_constraint("ruleset", rfile)
        if cie != 0:
            flash("ERROR, ruleset exists: %s " % (rfile), "error")
            return (redirect("/rules/rulesets/"))

        rnew = NaxsiRuleSets(rfile, rname, "naxsi-ruleset: %s" % rfile, 0, ts)
        db.session.add(rnew)
        try:
            db.session.commit()
            flash("OK created: %s " % (rfile), "success")
        except IntegrityError:
            flash("ERROR while trying to create ruleset: %s " % (rfile), "error")

        flash("OK created: %s " % (rfile), "success")

    return (redirect("/rules/rulesets/"))


@rules.route("/rulesets/plain/<path:rid>")
def ruleset_plain(rid=0):
    if rid == 0:
        return (redirect("/rulesets/"))
    r = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
    out_dir = current_app.config["RULES_EXPORT"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access EXPORT_DIR: %s " % (out_dir), "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return (redirect("/rules/rulesets/"))

    rf = "%s/naxsi/%s" % (out_dir, r.file)
    rf = "%s/naxsi/%s" % (out_dir, r.file)
    if not os.path.isfile(rf):
        flash("ERROR while trying to read %s " % (rf), "error")
        return (redirect("/rules/rulesets/"))

    rout = "".join(open(rf, "r"))
    return Response(rout, mimetype='text/plain')


@rules.route("/select/<path:selector>", methods=["GET"])
def nx_select(selector=0):
    if selector == 0:
        return (redirect("/rules/"))
    sel = str(selector)
    print "sel: %s " % sel[0:]
    try:
        rs_val = sel.split(":")[1]
    except:
        return (redirect("/rules/"))

    if sel[0:2] == "r:":
        rs_val = sel.split(":")[1]
        rules = NaxsiRules.query.filter(NaxsiRules.ruleset == rs_val).order_by(NaxsiRules.sid.desc()).all()
        selezion = "Search ruleset: %s " % rs_val
    elif sel[0:3] == "id:":
        rules = NaxsiRules.query.filter(NaxsiRules.sid == rs_val).order_by(NaxsiRules.sid.desc()).all()
        selezion = "Search sid: %s " % rs_val
    else:
        return (redirect("/rules/"))

    return (render_template("rules/index.html", rules=rules, selection=selezion))


@rules.route("/search/", methods=["GET"])
def search():
    srch = request.args.get('s', '').replace("+", "---")
    sclean = ""
    if len(srch) > 2:
        for cc in srch:
            if cc not in seeds.allowed_chars:
                print " >> not allowed char: %s" % cc
                # return(dx_all)
            else:
                sclean = "%s%s" % (sclean, cc)
        try:
            sclean = int(sclean)
            rules = db.session.query(NaxsiRules).filter(NaxsiRules.sid == sclean).all()
        except:
            sclean = sclean.replace("---", "%")
            sclean = "%" + sclean + "%"
            rules = db.session.query(NaxsiRules).filter(
                db.or_(NaxsiRules.msg.like(sclean), NaxsiRules.rmks.like(sclean),
                       NaxsiRules.detection.like(sclean))).order_by(NaxsiRules.sid.desc()).all()
    else:
        return (redirect("/rules/"))
    selz = "Search: %s" % srch
    # rules = db.session.query(NaxsiRules).filter(db.or_(NaxsiRules.msg.like(sclean), NaxsiRules.rmks.like(sclean), NaxsiRules.detection.like(sclean))).order_by(NaxsiRules.sid.desc()).all()
    return (render_template("rules/index.html", rules=rules, selection=selz,
                            lsearch=request.args.get('s', '')))


@rules.route("/new", methods=["GET", "POST"])
def new():
    next_sid = check_or_get_latest_sid()

    if request.method == "POST":
        # create new rule
        ts = int(time())
        nr = request.form
        doit = 1
        # ~ try:
        # processing vals
        print nr
        msg = nr["msg"]
        detect = str(nr["detection"]).strip()
        print "detect: %s " % detect[0:5]
        if detect[0:4] == "str:":
            pass
        elif detect[0:3] == "rx:":
            pass
        else:
            detect = "str:%s" % detect
        mz = "|".join(nr.getlist("mz"))
        try:
            if nr["custom_mz"] == "on":
                mz = "%s|%s" % (mz, nr["custom_mz_val"])
        except:
            pass
        score_raw = nr["score"].strip()
        score_val = nr["score_%s" % score_raw].strip()
        score = "%s:%s" % (score_raw, score_val)
        sid = next_sid
        rmks = nr["rmks"]
        ruleset = nr["ruleset"]
        negative = nr["negative"]
        if negative == "on":
            negative = 1
        else:
            negative = 0

            # ~ except:
            # ~ flash("""ERROR - please select MZ/Score
            # ~ <a class="btn btn-warning btn-lg" href="javascript:window.history.back()">Go Back</a>
            # ~ """, "error")
            # ~ doit = 0
        # ~
        if doit == 1:
            try:
                nrule = NaxsiRules(msg, detect, mz, score, sid, ruleset, rmks, "1", negative, ts)
                db.session.add(nrule)
                db.session.commit()
                flash("OK: created %s : %s" % (sid, msg), "success")
                return (redirect("/rules/edit/%s" % sid))
            except:
                flash("ERROR while trying to create %s : %s" % (sid, msg), "error")

        return (redirect("/rules/new"))

    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
    score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
    rulesets = NaxsiRuleSets.query.all()

    return (render_template("rules/new.html",
                            mz=mz,
                            rulesets=rulesets,
                            score=score,
                            latestn=next_sid
                            ))


@rules.route("/edit/<path:sid>", methods=["GET", "POST"])
def edit(sid=0):
    if sid == 0:
        return (redirect("/rules/"))

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return (redirect("/rules/"))
    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
    score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
    rulesets = NaxsiRuleSets.query.all()
    rruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == rinfo.ruleset).first()
    custom_mz = ""
    mz_check = rinfo.mz
    if re.search("^\$[A-Z]+:(.*)\|[A-Z]+", mz_check):
        custom_mz = mz_check
        rinfo.mz = "custom"
    return (render_template("rules/edit.html",
                            mz=mz,
                            rulesets=rulesets,
                            score=score,
                            rules_info=rinfo,
                            rule_ruleset=rruleset,
                            custom_mz=custom_mz
                            ))


@rules.route("/save/<path:sid>", methods=["POST"])
@demo_mode("")
def save(sid=0):
    if sid == 0:
        return (redirect("/rules/"))

    if request.method == "POST":
        # create new rule
        ts = int(time())
        nr = request.form
        doit = 1
        try:
            msg = nr["msg"]
            detect = str(nr["detection"]).strip()
            print "detect: %s " % detect[0:4]
            if detect[0:4] == "str:":
                pass
            elif detect[0:3] == "rx:":
                pass
            else:
                detect = "str:%s" % detect
            mz = "|".join(nr.getlist("mz"))
            try:
                if nr["custom_mz"] == "on":
                    if len(mz) > 1:
                        mz = "%s|%s" % (nr["custom_mz_val"], mz)
                    else:
                        mz = "%s" % (nr["custom_mz_val"])
            except:
                pass
            score_raw = nr["score"].strip()
            score_val = nr["score_%s" % score_raw].strip()
            score = "%s:%s" % (score_raw, score_val)
            # sid = nr["sid"]
            rmks = nr["rmks"]
            ruleset = nr["ruleset"]
            active = nr["active"]
            negative = nr["negative"]
            if negative == "on":
                negative = 1
            else:
                negative = 0

        except:
            flash("""ERROR - please select MZ/Score
    <a href="javascript:alert(history.back)">Go Back</a>
      """, "error")
            doit = 0

        if doit == 1:
            nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
            nrule.msg = msg
            nrule.detection = detect
            nrule.mz = mz
            nrule.score = score
            nrule.ruleset = ruleset
            nrule.rmks = rmks
            nrule.active = active
            nrule.negative = negative
            nrule.timestamp = ts
            db.session.add(nrule)
            nruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == nrule.ruleset).first()
            nruleset.updated = 1
            db.session.add(nruleset)
            try:
                db.session.commit()
                flash("OK: updated %s : %s" % (sid, msg), "success")
            except:
                flash("ERROR while trying to update %s : %s" % (sid, msg), "error")
    return (redirect("/rules/edit/%s" % sid))


@rules.route("/view/<path:sid>", methods=["GET"])
def view(sid=0):
    if sid == 0:
        return (redirect("/rules/"))

    rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not rinfo:
        return (redirect("/rules/"))
    rtext = z_display_rule(rinfo, full=0)
    return (render_template("rules/view.html",
                            rule=rinfo,
                            rtext=rtext
                            ))


@rules.route("/del/<path:sid>", methods=["GET"])
@demo_mode("")
def del_sid(sid=0):
    if sid == 0:
        return (redirect("/rules/"))

    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
    if not nrule:
        return (redirect("/rules/"))

    nruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == nrule.ruleset).first()
    nruleset.updated = 1
    db.session.add(nruleset)
    db.session.delete(nrule)
    try:
        db.session.commit()
        flash("OK: deleted %s : %s" % (sid, nrule.msg), "success")
    except:
        flash("ERROR while trying to update %s : %s" % (sid, nrule.msg), "error")

    return (redirect("/rules/"))


@rules.route("/deact/<path:sid>", methods=["GET"])
@demo_mode("")
def deact_sid(sid=0):
    if sid == 0:
        return (redirect("/rules/"))

    nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()

    if not nrule:
        return (redirect("/rules/"))
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
        return (redirect("/rules/"))
    mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
    score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
    rulesets = NaxsiRuleSets.query.all()
    return (render_template("rules/edit.html",
                            mz=mz,
                            rulesets=rulesets,
                            score=score,
                            rules_info=rinfo
                            ))


@rules.route("/export/", methods=["GET"])
@rules.route("/export/<path:rid>", methods=["GET"])
def export_ruleset(rid=0):
    out_dir = current_app.config["RULES_EXPORT"]
    naxsi_out = "%s/naxsi" % out_dir
    ossec_out = "%s/ossec" % out_dir
    export_date = strftime("%F - %H:%M", localtime(time()))
    if rid == 0:
        rid = "all"

    if rid == "all":
        rsets = NaxsiRuleSets.query.filter(NaxsiRuleSets.updated != 0).all()
    else:
        rsets = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).all()

    if not rsets:
        flash("Nothing to export, no rules changed", "success")
        return (redirect("/rules/rulesets/"))

    # naxsi-exports
    for rs in rsets:
        of = "%s/%s" % (naxsi_out, rs.file)
        print "> exporting %s" % of
        try:
            f = open(of, "w")
            head = current_app.config["RULESET_HEADER"].replace("RULESET_DESC", rs.name).replace("RULESET_FILE",
                                                                                                 rs.file).replace(
                "RULESET_DATE", export_date)
            f.write(head)
        except:
            flash("ERROR while trying to export %s" % rs.file, "error")
            return (redirect("/rules/"))
        rules = NaxsiRules.query.filter(NaxsiRules.ruleset == rs.file, NaxsiRules.active == 1).order_by(
            NaxsiRules.sid.desc()).all()
        nxruleset = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == rs.file).first()
        nxruleset.updated = 0
        db.session.add(nxruleset)
        db.session.commit()
        for rule in rules:
            rout = z_display_rule(rule)
            f.write("%s \n" % rout)
        f.close()
        flash("Exported: %s / %s" % (rid, of), "success")

    return (redirect("/rules/rulesets/"))


@rules.route("/import/", methods=["GET", "POST"])
@demo_mode("")
def import_ruleset():
    out_dir = current_app.config["RULES_EXPORT"]
    import_date = strftime("%F - %H:%M", localtime(time()))
    if request.method == "GET":
        rulesets = NaxsiRuleSets.query.all()
        return (render_template("rules/import.html", rulesets=rulesets))

    elif request.method == "POST":

        # create new rule
        ts = int(time())
        nr = request.form
        rset = nr["ruleset"].strip().lower()
        rcust = nr["cruleset"].strip().lower()
        if len(rcust) > 4:
            rset = rcust
            flash("creating new ruleset for import: %s" % rcust, "success")
            rname = rset.split(".")[0].upper()
            rnew = NaxsiRuleSets(rset, rname, "naxsi-ruleset: %s" % rcust, ts)
            db.session.add(rnew)
            db.session.commit()
            flash("OK created: %s " % (rset), "success")

        rin = nr["rules"]

        for r in rin.split("\n"):
            r = r.strip()
            if len(r) < 30:
                continue
            elif r[0] == "#":
                continue
            # TODO better with re.match()
            elif r[0:8] != "MainRule":
                continue
            flash("importing: %s" % (r), "success")
            msg = detect = mz = score = sid = 0
            rs = r.split("\"")
            print rs
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

            known_sid = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
            if known_sid:
                old_sid = sid
                sid = check_or_get_latest_sid(old_sid)
                flash("changing sid: orig: %s / new: %s" % (old_sid, sid), "success")
                rmks = "%s \nchanged sid: orig: %s / new: %s " % (rmks, old_sid, sid)

            nrule = NaxsiRules(msg, detect, mz, score, sid, rset, rmks, "1", ts)
            db.session.add(nrule)
            db.session.commit()
            flash("OK: created %s : %s" % (sid, msg), "success")

    return (redirect("/rules/export/"))


@rules.route("/backup/", methods=["GET"])
def rules_backup_view(action="show"):
    out_dir = current_app.config["BACKUP_DIR"]
    sqlite_bin = current_app.config["SQLITE_BIN"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access BACKUP_DIR: %s " % (out_dir), "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return (redirect("/rules/"))

    bfiles = {}
    bfiles_in = glob("%s/*.sql.*" % out_dir)
    print bfiles_in
    for b in bfiles_in:
        bx = b.split("/")
        print bx
        bname = bx[-1]
        bid = bx[-1].split(".")[-1]
        bdate = strftime("%F - %H:%M", localtime(float(bx[-1].split(".")[-1])))
        bfiles[bid] = [bname, bdate]

    return (render_template("rules/backups.html",
                            bfiles=bfiles
                            ))


@rules.route("/backup/<path:action>", methods=["GET"])
@demo_mode("")
def rules_backup(action="show"):
    out_dir = current_app.config["BACKUP_DIR"]
    sqlite_bin = current_app.config["SQLITE_BIN"]

    if not os.path.isdir(out_dir):
        flash("ERROR while trying to access BACKUP_DIR: %s " % (out_dir), "error")
        flash("you might want to adjust your <a href=\"/settings\">Settings</a> ", "error")
        return (redirect("/rules/"))

    if action == "create":
        bdate = int(time())
        bfile = "%s/rules.sql.%s" % (out_dir, bdate)
        rules_db = "spike/rules.db"
        if os.path.isfile(sqlite_bin) and os.access(sqlite_bin, os.X_OK):
            pass
        else:
            flash("ERROR, no sqlite_bin found in: %s " % sqlite_bin, "error")
            flash("you might want to adjust your <a href=\"/settings\">Settings</a> and install sqlite", "error")
            return (redirect("/rules/backup"))

        f = open(bfile, "w")
        f.write("-- spike-dump %s \n\n" % strftime("%F - %H:%M", localtime(float(bdate))))
        f.close()

        try:
            os.system("%s %s  .dump >> %s" % (sqlite_bin, rules_db, bfile))
            flash("creating backup %s" % bdate, "success")
            flash("backup OK in %s" % bfile, "success")
        except:
            flash("ERRORwhile executing dump %s " % bfile, "error")
            return (redirect("/rules/backup"))
        return (redirect("/rules/backup"))

    elif action == "show":

        bfiles = {}
        bfiles_in = glob("%s/*.sql.*" % out_dir)
        print bfiles_in
        for b in bfiles_in:
            bx = b.split("/")
            print bx
            bname = bx[-1]
            bid = bx[-1].split(".")[-1]
            bdate = strftime("%F - %H:%M", localtime(float(bx[-1].split(".")[-1])))
            bfiles[bid] = [bname, bdate]

        return (render_template("rules/backups.html",
                                bfiles=bfiles
                                ))

    elif action == "reload":
        try:
            bid = request.args.get('bid')

        except:
            flash("ERROR, no backup - id selected ", "error")
            return (redirect("/rules/backup"))

        bfile = "%s/rules.sql.%s" % (out_dir, bid)
        rules_db = "spike/rules.db"

        if os.path.isfile(sqlite_bin) and os.access(sqlite_bin, os.X_OK):
            pass
        else:
            flash("ERROR, no sqlite_bin found in: %s " % sqlite_bin, "error")
            flash("you might want to adjust your <a href=\"/settings\">Settings</a> and install sqlite", "error")
            return (redirect("/rules/backup"))

        try:
            os.unlink(rules_db)
            os.system("%s %s < %s" % (sqlite_bin, rules_db, bfile))
            flash("restored db.backup < %s" % bfile, "success")
        except:
            flash("ERRORwhile executing dump %s " % bfile, "error")
            return (redirect("/rules/backup"))
        return (redirect("/rules/backup"))


    elif action == "display":
        try:
            bid = request.args.get('bid')

        except:
            flash("ERROR, no backup - id selected ", "error")
            return (redirect("/rules/backup"))

        if not os.path.isfile("%s/rules.sql.%s" % (out_dir, bid)):
            flash("ERROR, no backup found for id: %s" % bid, "error")
            return (redirect("/rules/backup"))

        out = "".join(open("%s/rules.sql.%s" % (out_dir, bid), "r").readlines())
        return Response(out, mimetype='text/plain')

    elif action == "delete":
        try:
            bid = request.args.get('bid')

        except:
            flash("ERROR, no backup - id selected ", "error")
            return (redirect("/rules/backup"))

        if not os.path.isfile("%s/rules.sql.%s" % (out_dir, bid)):
            flash("ERROR, no backup found for id: %s" % bid, "error")
            return (redirect("/rules/backup"))

        os.unlink("%s/rules.sql.%s" % (out_dir, bid))
        flash("backup deleted: %s/rules.sql.%s" % (out_dir, bid), "success")


    else:
        flash("ERROR, no backup - action selected ", "error")
        return (redirect("/rules/backup"))
    return (redirect("/rules/backup"))


def z_display_rule(rule, full=1):
    nout = "unknown"
    rdate = strftime("%F - %H:%M", localtime(float(str(rule.timestamp))))
    rmks = "# ".join(rule.rmks.strip().split("\n"))
    if rule.detection[0:4] == "str:":
        detect = rule.detection.lower()
    else:
        detect = rule.detection
    negate = ""
    if rule.negative == 1:
        negate = "negative"
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

    return (nout)
