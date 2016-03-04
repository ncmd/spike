from spike.model import db


class NaxsiRuleSets(db.Model):
    __bind_key__ = 'rules'
    __tablename__ = 'naxsi_rulesets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024), nullable=False, unique=True)
    remarks = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)
    db.UniqueConstraint('name')

    def __init__(self, name, remarks, timestamp):
        self.name = name
        self.remarks = remarks
        self.timestamp = timestamp
