import os

from flask import current_app, Blueprint, render_template, request, redirect, flash

from spike.model import *
from spike.views  import demo_mode

settings = Blueprint('settings', __name__, url_prefix = '/settings')

@settings.route("/")
def index():
  settings = Settings.query.order_by(Settings.name).all()
  if not settings:
    return(redirect("/rules"))
  return(render_template("settings/index.html", settings = settings))

@settings.route("/mz")
def mz_index():
  mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").order_by(ValueTemplates.value).all()
  if not mz:
    return(redirect("/settings"))
  return(render_template("settings/mz.html", mz = mz))


@settings.route("/sql",  methods = ["GET", "POST"])
@demo_mode("")
def execute_sql():
  res = []
  sqle = ""

  if request.method == "POST":
    rsql = request.form
    sqle = [] 
    sql = rsql["sql"].split("\n")
    out = 0
    for s in sql:
      s = s.strip()
      if len(s) < 20: 
        flash("query is too short", "error")
        return(redirect("/settings/sql"))
      if s[-1] != ";":
        s = "%s ;" % s
      if s[0:10].find("select") > -1:
        out = 1
        
      sqle.append(s)
    if out == 1:
      try:
        res = db.session.execute("\n".join(sqle), bind=db.get_engine(current_app, 'rules')).fetchall()
      except:
        flash("ERROR while trying to execute : %s" % ("\n".join(sqle)), "error")

    else:
      db.session.execute("\n".join(sqle), bind=db.get_engine(current_app, 'rules'))
      db.session.commit()
      res = [("OK",  "\n".join(sqle))]
  return(render_template("settings/sql.html", res = res, sqlval = "\n".join(sqle)))


@settings.route("/mz/del", methods = ["POST"])
@demo_mode("")
def mz_del():
  nd = request.form
  mzid = nd["mzid"]


  dmz = ValueTemplates.query.filter(ValueTemplates.id == mzid).first()
  if not dmz:
    flash("Nothing found in %s " % (mzid), "error")
    return(redirect("/settings/mz"))
  
  db.session.delete(dmz)
  try:
    db.session.commit()
    flash("OK: deleted %s " % (dmz.value), "success")
  except:
    flash("ERROR while trying to delete : %s" % (dmz.value ), "error")
  return(redirect("/settings/mz"))


@settings.route("/mz/new", methods = ["POST"])
@demo_mode("")
def mz_new():
  nd = request.form
  nmz = nd["nmz"]
  mz = ValueTemplates("naxsi_mz", nmz)
  db.session.add(mz)
  db.session.commit()
  flash("Updated MZ: %s" % nmz, "success")  
  return(redirect("/settings/mz"))

@settings.route("/scores")
def score_index():
  sc = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").order_by(ValueTemplates.value).all()
  if not sc:
    return(redirect("/settings"))
  return(render_template("settings/scores.html", scores = sc))

@settings.route("/scores/new", methods = ["POST"])
@demo_mode("")
def score_new():
  nd = request.form
  nsc = nd["nscore"]
  if nsc[0] != "$":
    nsc = "$%s" % nsc
  sc = ValueTemplates("naxsi_score", nsc.upper())
  db.session.add(sc)
  db.session.commit()
  flash("Updated Score: %s" % nsc, "success")  
  return(redirect("/settings/scores"))


@settings.route("/scores/del", methods = ["POST"])
@demo_mode("")
def scores_del():
  nd = request.form
  scid = nd["scid"]
  dsc = ValueTemplates.query.filter(ValueTemplates.id == scid).first()
  if not dsc:
    flash("Nothing found in %s " % (scid), "error")
    return(redirect("/settings/scores"))  
  db.session.delete(dsc)
  try:
    db.session.commit()
    flash("OK: deleted %s " % (dsc.value), "success")
  except:
    flash("ERROR while trying to delete : %s" % (dsc.value ), "error")
  return(redirect("/settings/scores"))


@settings.route("/update")
@demo_mode("")
def mz_update():
  out = "".join(os.popen("./server update"))
  flash("OK: update " , "success")
  
  return(render_template("layouts/pre.html", text = out, title="Spike-Update"))
  

@settings.route("/save", methods = ["POST"])
@demo_mode("")
def save_settings():
  
  sform = request.form
  for s in sform:
    sfind = Settings.query.filter(Settings.name == s).first()
    if not sfind:
      print "> no value for %s" % sfind
      continue
    if sfind.value != sform[s]:
      sfind.value = sform[s]
      db.session.add(sfind)
  flash("Updated setting: %s" % s, "success")
  db.session.commit()
  os.system("touch spike/__init__.py")
  return(redirect("/settings"))
  

@settings.route("/<path:szone>")
def szone(szone=0):
  return(render_template("notyet.html", text = ""))

