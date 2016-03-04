from spike.model import db


class NaxsiRuleSets(db.Model):
    __bind_key__ = 'rules'
    __tablename__ = 'naxsi_rulesets'
    __table_args__ = (db.UniqueConstraint('file', 'name'), {})  # seems not top work with sqlalchemy?

    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(1024), nullable=False, unique=True)
    name = db.Column(db.String(1024), nullable=False, unique=True)
    remarks = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)
    db.UniqueConstraint('file', 'name')

    def __init__(self, file, name, remarks, timestamp):
        self.file = file
        self.name = name
        self.remarks = remarks
        self.timestamp = timestamp