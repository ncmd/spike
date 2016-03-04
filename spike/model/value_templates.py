from spike.model import db


class ValueTemplates(db.Model):
    __bind_key__ = 'rules'
    __tablename__ = 'value_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024), nullable=False)
    value = db.Column(db.String(1024), nullable=False)

    def __init__(self, name, value):
        self.name = name
        self.value = value
