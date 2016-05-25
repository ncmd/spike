import re
from shlex import shlex

from flask import url_for

from spike.model import db
from spike.model.naxsi_rules import NaxsiRules

from nxapi import whitelist


class NaxsiWhitelist(db.Model):
    __bind_key__ = 'rules'
    __tablename__ = 'naxsi_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    wl = db.Column(db.String, nullable=False)
    mz = db.Column(db.String(1024), nullable=False)
    negative = db.Column(db.Integer, nullable=False, server_default='0')
    active = db.Column(db.Integer, nullable=False, server_default='1')
    timestamp = db.Column(db.Integer, nullable=False)
    whitelistset = db.Column(db.String(1024), nullable=False)

    def __init__(self, wl='0', mz='', active=0, negative=0, whitelistset='', timestamp=0):
        self.wl = wl
        self.mz = mz
        self.active = active
        self.negative = negative
        self.whitelistset = whitelistset
        self.timestamp = timestamp
        self.warnings = []
        self.errors = []

    def from_dict(self, d):
        for key, value in d.items():
            setattr(self, key, value)
        return self

    def __str__(self):
        return 'BasicRule {} wl:{} "mz:{}";'.format('negative' if self.negative else '', self.wl, self.mz)

    def parse(self, str_wl):
        return whitelist.parse(str_wl)

    def validate(self):
        return whitelist.validate(self.__dict__)

    def explain(self):
        return whitelist.explain(self.__dict__)
