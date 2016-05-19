from time import strftime, localtime

from spike.model import db

from nxapi import rules


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
    rmks = db.Column(db.Text, nullable=True, server_default="")
    active = db.Column(db.Integer, nullable=False, server_default="1")
    negative = db.Column(db.Integer, nullable=False, server_default='0')
    timestamp = db.Column(db.Integer, nullable=False)

    mr_kw = ["MainRule", "BasicRule", "main_rule", "basic_rule"]
    static_mz = {"$ARGS_VAR", "$BODY_VAR", "$URL", "$HEADERS_VAR"}
    full_zones = {"ARGS", "BODY", "URL", "HEADERS", "FILE_EXT", "RAW_BODY"}
    rx_mz = {"$ARGS_VAR_X", "$BODY_VAR_X", "$URL_X", "$HEADERS_VAR_X"}
    sub_mz = list(static_mz) + list(full_zones) + list(rx_mz)

    def __init__(self, msg="", detection="str:a", mz="ARGS", score="$None:0", sid='42000', ruleset="", rmks="",
                 active=0, negative=False, timestamp=0):
        self.msg = msg
        self.detection = detection
        self.mz = mz
        self.score = score
        self.sid = sid
        self.ruleset = ruleset
        self.rmks = rmks
        self.active = active
        self.negative = negative
        self.timestamp = timestamp
        self.warnings = []
        self.errors = []

    def from_dict(self, d):
        for key, value in d.items():
            if key == 'mz' and isinstance(value, list):
                value = '|'.join(value)
            setattr(self, key, value)
        return self

    def fullstr(self):
        rdate = strftime("%F - %H:%M", localtime(float(str(self.timestamp))))
        rmks = "# ".join(self.rmks.strip().split("\n"))
        return "#\n# sid: {0} | date: {1}\n#\n# {2}\n#\n{3}".format(self.sid, rdate, rmks, str(self))

    def __str__(self):
        return rules.short_str(self.__dict__)

    def explain(self):
        return rules.explain(self.__dict__)

    def validate(self):
        return rules.validate(self.__dict__)

    def parse_rule(self, full_str):
        return rules.parse_rule(full_str)
