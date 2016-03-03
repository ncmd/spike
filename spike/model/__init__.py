from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from naxsi_rules import NaxsiRules, NaxsiRuleSets, ValueTemplates
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


def check_or_get_latest_sid(sid=0):  # FIXME I'm ugly as fuck
    if sid == 0:
        latest = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        if not latest:
            latest = Settings.query.filter(Settings.name == "rules_offset").first()
            latest = int(latest.value)
        else:
            latest = latest.sid
        lsid = latest + 1
    else:
        is_known = NaxsiRules.query.filter(NaxsiRules.sid == sid).first()
        if not is_known:
            lsid = sid
        else:
            latest = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
            if not latest:
                latest = Settings.query.filter(Settings.name == "rules_offset").first()
                latest = int(latest.value)
            else:
                latest = latest.sid
            lsid = latest + 1
    return lsid
