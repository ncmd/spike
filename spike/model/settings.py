from spike.model import db


class Settings(db.Model):
  __bind_key__ = 'settings'
  __tablename__ = 'settings'
  
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False, unique = True)
  value = db.Column(db.String(), nullable=False, server_default = "")

  def __init__(self, name, value):
    self.name = name 
    self.value = value  
