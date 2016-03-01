from spike.model import db


class NaxsiRules(db.Model):
  __bind_key__ = 'rules'
  __tablename__ = 'naxsi_rules'
  
  id = db.Column(db.Integer, primary_key=True)
  msg = db.Column(db.String(), nullable=False)
  detection = db.Column(db.String(1024), nullable=False)
  mz = db.Column(db.String(1024), nullable=False)
  score = db.Column(db.String(1024), nullable=False)
  sid = db.Column(db.Integer, nullable=False, unique=True)
  ruleset = db.Column(db.String(1024), nullable=False)
  rmks = db.Column(db.Text, nullable=True, server_default = "")
  active  = db.Column(db.Integer, nullable=False, server_default = "1")
  negative  = db.Column(db.Integer, nullable=False, server_default = '0')  
  timestamp  = db.Column(db.Integer, nullable=False)
  


  def __init__(self, msg, detection, mz, score, sid, ruleset, rmks, active,  negative, timestamp):
    self.msg = msg
    self.detection = detection 
    self.mz = mz
    self.score =  score 
    self.sid =  sid 
    self.ruleset =  ruleset 
    self.rmks  =  rmks 
    self.active  =  active
    self.negative = negative
    self.timestamp =  timestamp   


class NaxsiRuleSets(db.Model):
  __bind_key__ = 'rules'
  __tablename__ = 'naxsi_rulesets'
  __table_args__ = ( db.UniqueConstraint('file', 'name'), {}) # seems not top work with sqlalchemy?
  
  id = db.Column(db.Integer, primary_key=True)
  file = db.Column(db.String(1024), nullable=False, unique=True)
  name = db.Column(db.String(1024), nullable=False, unique=True)
  remarks = db.Column(db.Text, nullable=False)
  timestamp = db.Column(db.Integer, nullable=False)
  updated = db.Column(db.Integer, nullable=False)
  db.UniqueConstraint('file', 'name')

  def __init__(self, file, name, remarks, updated, timestamp):
    self.file = file 
    self.name = name 
    self.remarks = remarks 
    self.updated = updated 
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


