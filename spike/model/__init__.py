from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from naxsi_rules import NaxsiRules, NaxsiRuleSets
from settings import Settings


def check_constraint(ctype, value):
    if ctype == "settings":
        cres = Settings.query.filter(Settings.name == value).first()
    elif ctype == "ruleset":
        cres = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == value).first()
    else:
        cres = 1

    if not cres:
        return 0
    return (cres)


def get_latest_sid():  # FIXME I'm ugly as fuck
    latest = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
    if latest is None:
        latest = Settings.query.filter(Settings.name == "rules_offset").first()
        return int(latest.value) + 1
    return latest.sid + 1
