import re

from spike.model import db
from shlex import shlex

from spike.model.naxsi_rules import NaxsiRules
from flask import url_for


class NaxsiWhitelist(db.Model):
    __bind_key__ = 'rules'
    __tablename__ = 'naxsi_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    wid = db.Column(db.String, nullable=False, unique=True)
    mz = db.Column(db.String(1024), nullable=False)
    negative = db.Column(db.Integer, nullable=False, server_default='0')
    active = db.Column(db.Integer, nullable=False, server_default='1')
    timestamp = db.Column(db.Integer, nullable=False)
    whitelistset = db.Column(db.String(1024), nullable=False)

    def __init__(self, wid='0', mz='', active=0, negative=0, whitelistset='', timestamp=0):
        self.wid = wid
        self.mz = mz
        self.active = active
        self.negative = negative
        self.whitelistset = whitelistset
        self.timestamp = timestamp
        self.warnings = []
        self.error = []

    def __str__(self):
        return 'BasicRule {}wl:{} "mz:{}";'.format('negative ' if self.negative else ' ', self.wid, self.mz)

    def __validate_id(self, wid):
        if not re.match(r'(\-?\d+,)*\-?\d+', wid):
            self.error.append('Illegal character in the whitelist id.')
            return False
        self.wid = wid
        return True

    def __validate_mz(self, mz):
        # Borrow '__validate_matchzone' from naxsi_rules.py ?
        self.mz = mz
        return True

    def parse(self, str_wl):
        self.warnings = list()
        self.error = list()

        lexer = shlex(str_wl)
        lexer.whitespace_split = True
        split = list(iter(lexer.get_token, ''))

        for piece in split:
            if piece == ';':
                continue
            elif piece.startswith(('"', "'")) and (piece[0] == piece[-1]):  # remove (double-)quotes
                piece = piece[1:-1]

            if piece == 'BasicRule':
                continue
            elif piece.startswith('wl:'):
                self.__validate_id(piece[3:])
            elif piece.startswith('mz:'):
                self.__validate_mz(piece[3:])
            elif piece == 'negative':
                self.negative = True
            else:
                self.error.append('Unknown fragment: {}'.format(piece))
                return False

        if 'BasicRule' not in split:
            self.error.append("No 'BasicRule' keyword in {}".format(str_wl))
            return False

        return True

    def validate(self):
        return True

    def explain(self):
        def __linkify_rule(rid):
            if NaxsiRules.query.filter(NaxsiRules.sid == self.wid).first() is None:
                return rid
            return '<a href="{}">{}</a>'.format(url_for('rules.view', sid=rid), self.wid)

        if self.wid == '0':
            ret = 'Whitelist all rules'
        elif self.wid.isdigit():
            ret = 'Whitelist the rule {}'.format(__linkify_rule(self.wid))
        else:
            zones = list()
            for rid in self.wid.split(','):
                if rid.startswith('-'):
                    zones.append('except the rule {}'.format(__linkify_rule(rid[1:])))
                else:
                    zones.append('the rule {}'.format(__linkify_rule(rid)))
            ret = 'Whitelist '+ ', '.join(zones)

        if not self.mz:
            return ret + '.'

        return ret + ' if matching in {}.'.format(self.mz)
