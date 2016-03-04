from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from naxsi_rules import NaxsiRules, NaxsiRuleSets


def check_constraint(ctype, value):
    if ctype == "ruleset":
        cres = NaxsiRuleSets.query.filter(NaxsiRuleSets.file == value).first()
    else:
        cres = 1

    if not cres:
        return 0
    return cres