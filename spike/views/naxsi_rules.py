from flask import current_app, Blueprint, render_template, abort, request, redirect, url_for, flash, Response 
from flask.ext.login import login_user, logout_user, current_user, login_required
import simplejson as json
import os 
from time import time, localtime, strftime
from uuid import uuid4 


from spike.views import role_required, date_id, csp_id
from spike import seeds 
from spike.model import *

naxsi_rules = Blueprint('naxsi_rules', __name__, url_prefix = '/rules')

@naxsi_rules.route("/")
def index():
  rules = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).all()
  return(render_template("rules/index.html", rules = rules))

@naxsi_rules.route("/rulesets/")
def rulesets():
  rulesets = NaxsiRuleSets.query.order_by(NaxsiRuleSets.name).all()
  return(render_template("rules/rulesets.html", rulesets = rulesets))

@naxsi_rules.route("/rulesets/view/<path:rid>")
def ruleset_view(rid = 0):

  if rid == 0:
    return(redirect("/rulesets/"))
  r = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).first()
  out_dir = current_app.config["NAXSI_RULES_EXPORT"]
  rf = "%s/%s" % ( out_dir, r.file)
  if not os.path.isfile(rf):
    flash("ERROR while trying to read %s " % (rf), "error")
    return(redirect("/rulesets/"))

  rout = "". join(open(rf, "r"))
  
  return(render_template("rules/ruleset_view.html", r = r, rout = rout))


@naxsi_rules.route("/select/<path:selector>",  methods = ["GET"])
def nx_select(selector=0):
  if selector == 0:
    return(redirect("/rules/"))
  sel = str(selector)
  print "sel: %s " % sel[0:]
  try:
    rs_val = sel.split(":")[1]
  except:
    return(redirect("/rules/"))
    
  if sel[0:2] == "r:":
    rs_val = sel.split(":")[1]
    rules = NaxsiRules.query.filter(NaxsiRules.ruleset == rs_val).order_by(NaxsiRules.sid.desc()).all()
    selezion = "Search ruleset: %s " % rs_val
  elif sel[0:3] == "id:":
    rules = NaxsiRules.query.filter(NaxsiRules.sid == rs_val).order_by(NaxsiRules.sid.desc()).all()
    selezion = "Search sid: %s " % rs_val
  else: 
    return(redirect("/rules/"))

  return(render_template("rules/index.html", rules = rules, selection = selezion))


    
@naxsi_rules.route("/search/",  methods = ["GET"])
def search():
  from flask.ext.sqlalchemy import SQLAlchemy
  
  srch = request.args.get('s', '').replace("+", "---")
  sclean = ""
  if len(srch) > 2:
    for cc in srch:
      if cc not in seeds.allowed_chars:
        print " >> not allowed char: %s" % cc
        #return(dx_all)
      else:
        sclean = "%s%s" % (sclean, cc)
    sclean = sclean.replace("---", "%")
    sclean = "%" + sclean + "%"
  else:
    return(redirect("/rules/"))
  selz = "Search: %s" % srch
  rules = db.session.query(NaxsiRules).filter(db.or_(NaxsiRules.msg.like(sclean), NaxsiRules.rmks.like(sclean), NaxsiRules.detection.like(sclean))).order_by(NaxsiRules.sid.desc()).all()
  return(render_template("rules/index.html", rules = rules, selection = selz, 
      lsearch = request.args.get('s', '')))
  

    
@naxsi_rules.route("/new",  methods = ["GET", "POST"])
def new():

  latest = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
  if not latest:
    latest = current_app.config["NAXSI_RULES_OFFSET"]
  else:
    latest = latest.sid
  latestn = latest + 1


  if request.method == "POST":
    # create new rule
    ts = int(time())
    nr = request.form
    doit = 1
    try:
      # processing vals
      msg = nr["msg"]
      detect = str(nr["detection"]).strip()
      print "detect: %s " % detect[0:5]
      if detect[0:4] == "str:":
        pass 
      elif detect[0:3] == "rx:":
        pass 
      else:
        detect = "str:%s" % detect
      mz = nr["mz"]
      score_raw = nr["score"].strip()
      score_val = nr["score_%s" % score_raw].strip()
      score ="%s:%s" % (score_raw, score_val)      
      sid = latestn
      rmks = nr["rmks"]
      ruleset = nr["ruleset"]
      
    except:
      flash("""ERROR - please select MZ/Score
    <a class="btn btn-warning btn-lg" href="javascript:window.history.back()">Go Back</a>
      """, "error")
      doit = 0
    
    if doit == 1:
      try:
        nrule = NaxsiRules(msg, detect, mz, score, sid, ruleset, rmks, "1", ts)
        db.session.add(nrule)
        db.session.commit()
        flash("OK: created %s : %s" % (sid, msg), "success")
        latestn +=1 
        return(redirect("/rules/edit/%s" % sid))
      except:
        flash("ERROR while trying to create %s : %s" % (sid, msg), "error")

    return(redirect("/rules/new"))

      

  mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
  score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
  rulesets = NaxsiRuleSets.query.all()
  return(render_template("rules/new.html", 
      mz = mz, 
      rulesets = rulesets,
      score = score, 
      latestn = latestn
      ))

@naxsi_rules.route("/edit/<path:sid>",  methods = ["GET", "POST"])
def edit(sid=0):

  if sid == 0:
    return(redirect("/rules/"))

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
      mz = nr["mz"]
      score_raw = nr["score"].strip()
      score_val = nr["score_%s" % score_raw].strip()      
      score ="%s:%s" % (score_raw, score_val)    
      #sid = nr["sid"]
      rmks = nr["rmks"]
      ruleset = nr["ruleset"]
      active = nr["active"]
  
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
      nrule.timestamp = ts
      #NaxsiRules.query.update(NaxsiRules).where(NaxsiRules.sid == sid).values(nrule)
      db.session.add(nrule)
      try:
        db.session.commit()
        flash("OK: updated %s : %s" % (sid, msg), "success")
      except:
        flash("ERROR while trying to update %s : %s" % (sid, msg), "error")
      
  rinfo = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
  if not rinfo:
    return(redirect("/rules/"))
  mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
  score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
  rulesets = NaxsiRuleSets.query.all()
  return(render_template("rules/edit.html", 
      mz = mz, 
      rulesets = rulesets,
      score = score, 
      rules_info = rinfo
      ))


@naxsi_rules.route("/del/<path:sid>",  methods = ["GET"])
def del_sid(sid=0):

  if sid == 0:
    return(redirect("/rules/"))

  nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
  if not nrule:
    return(redirect("/rules/"))
  
  db.session.delete(nrule)
  try:
    db.session.commit()
    flash("OK: deleted %s : %s" % (sid, nrule.msg), "success")
  except:
    flash("ERROR while trying to update %s : %s" % (sid, nrule.msg), "error")
      

  return(redirect("/rules/"))


@naxsi_rules.route("/deact/<path:sid>",  methods = ["GET"])
def deact_sid(sid=0):

  if sid == 0:
    return(redirect("/rules/"))

  nrule = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()

  if not nrule:
    return(redirect("/rules/"))
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
    return(redirect("/rules/"))
  mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").all()
  score = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").all()
  rulesets = NaxsiRuleSets.query.all()
  return(render_template("rules/edit.html", 
      mz = mz, 
      rulesets = rulesets,
      score = score, 
      rules_info = rinfo
      ))

@naxsi_rules.route("/export/",  methods = ["GET"])
@naxsi_rules.route("/export/<path:rid>",  methods = ["GET"])
def export_ruleset(rid=0):
  out_dir = current_app.config["NAXSI_RULES_EXPORT"]
  export_date = strftime("%F - %H:%M", localtime(time()))
  if rid == 0:
    rid = "all"
    
  if rid == "all":
    rsets = NaxsiRuleSets.query.all()
  else:
    rsets = NaxsiRuleSets.query.filter(NaxsiRuleSets.id == rid).all()
  
  for rs in rsets:
    of = "%s/%s" % (out_dir, rs.file)
    print "> exporting %s" % of
    try:
      f = open(of, "w")
      head = seeds.ruleset_header % (rs.name, rs.file, export_date)
      f.write(head)
    except:
      flash("ERROR while trying to export %s" % rs.file, "error")
      return(redirect("/rules/"))
    rules = NaxsiRules.query.filter(NaxsiRules.ruleset == rs.file).order_by(NaxsiRules.sid.desc()).all()
    for rule in rules:
      rdate = strftime("%F - %H:%M", localtime(float(rule.timestamp)))
      rmks = "# ".join(rule.rmks.strip().split("\n"))
      f.write("""
#
# sid: %s | date: %s 
#
# %s
#
MainRule "%s" "msg:%s" "mz:%s" "s:%s" id:%s  ;
      
      """ % (rule.sid, rdate, rmks, rule.detection, rule.msg, rule.mz, rule.score, rule.sid ))
    f.close()
    flash("Exported: %s / %s" % (rid, of), "success")
    
  return(redirect("/rules/rulesets/"))
    
     
  
  



