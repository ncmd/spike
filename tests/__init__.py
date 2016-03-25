# Something that is untested is broken.

import unittest

from spike.model.naxsi_rules import NaxsiRules
from spike.model import db

from spike import create_app


class TestsThatNeedsRules(unittest.TestCase):
    """ A simple calss that create a rule before running tests, and destroy destroy it when the tests are over. """
    def setUp(self):
        app = create_app()
        db.init_app(app)
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.created_rules = list()
        self.__create_rule()

    def tearDown(self):
        self.__delete_rule()

    def __create_rule(self):
        """

        :return int: The id of the new rule
        """
        current_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        current_sid = 1337 if current_sid is None else current_sid.sid + 1

        db.session.add(NaxsiRules(u'POUET', 'str:test', u'BODY', u'$SQL:8', current_sid, u'WEB_APPS',
                                  u'f hqewifueiwf hueiwhf uiewh fiewh fhw', '1', True, 1457101045))
        db.session.commit()
        self.created_rules.append(current_sid)
        return int(current_sid)

    def __delete_rule(self, sid=None):
        if sid:
            db.session.delete(NaxsiRules.query.filter(sid == NaxsiRules.sid).first())
        for sid in self.created_rules:
            _rule = NaxsiRules.query.filter(sid == NaxsiRules.sid).first()
            if _rule:
                db.session.delete(_rule)
