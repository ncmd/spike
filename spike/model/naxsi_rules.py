from spike.model import db
from time import time 

class NaxsiRules(db.Model):
  __bind_key__ = 'rules'
  __tablename__ = 'naxsi_rules'
  
  id = db.Column(db.Integer, primary_key=True)
  msg = db.Column(db.String(), nullable=False)
  detection = db.Column(db.String(1024), nullable=False)
  mz = db.Column(db.String(1024), nullable=False)
  score = db.Column(db.String(1024), nullable=False)
  sid = db.Column(db.Integer, nullable=False)
  ruleset = db.Column(db.String(1024), nullable=False)
  rmks = db.Column(db.Text, nullable=True, server_default = "")
  active  = db.Column(db.Integer, nullable=False, server_default = "1")
  timestamp  = db.Column(db.Integer, nullable=False)


  def __init__(self, msg, detection, mz, score, sid, ruleset, rmks, active, timestamp):
    self.msg = msg
    self.detection = detection 
    self.mz = mz
    self.score =  score 
    self.sid =  sid 
    self.ruleset =  ruleset 
    self.rmks  =  rmks 
    self.active  =  active
    self.timestamp =  timestamp   


class NaxsiRuleSets(db.Model):
  __bind_key__ = 'rules'
  __tablename__ = 'naxsi_rulesets'
  
  id = db.Column(db.Integer, primary_key=True)
  file = db.Column(db.String(1024), nullable=False, unique=True)
  name = db.Column(db.String(1024), nullable=False, unique=True)
  remarks = db.Column(db.Text, nullable=False)
  timestamp = db.Column(db.Integer, nullable=False)


  def __init__(self, file, name, remarks, timestamp):
    self.file = file 
    self.name = name 
    self.remarks = remarks 
    self.timestamp =  timestamp   


class ValueTemplates(db.Model):
  __bind_key__ = 'rules'
  __tablename__ = 'value_templates'
  
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(1024), nullable=False)
  value = db.Column(db.String(1024), nullable=False)


  def __init__(self, name, value ):
    self.name = name 
    self.value = value 


