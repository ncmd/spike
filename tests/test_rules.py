from time import strftime, localtime
import re

from spike import create_app
from spike.model import db
from spike.model.naxsi_rules import NaxsiRules

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse

import unittest


class FlaskrTestCase(unittest.TestCase):
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
        self.created_rules.append(current_sid)
        return int(current_sid)

    def __delete_rule(self, sid=None):
        if sid:
            db.session.delete(NaxsiRules.query.filter(sid == NaxsiRules.sid).first())
        for sid in self.created_rules:
            _rule = NaxsiRules.query.filter(sid == NaxsiRules.sid).first()
            if _rule:
                db.session.delete(_rule)

    def test_index(self):
        rv = self.app.get('/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('<title>SPIKE! - WAF Rules Builder</title>', rv.data)
        self.assertTrue(re.search(r'<h2>Naxsi - Rules \( \d+ \)</h2>', rv.data) is not None)

    def test_view(self):
        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.get('/rules/view/%d' % _rule.sid)
        self.assertEqual(rv.status_code, 200)

        _sid = _rule.sid + 1
        rv = self.app.get('/rules/view/%d' % _sid)
        self.assertEqual(urlparse(rv.location).path, '/rules/')

    def test_new_rule(self):
        rv = self.app.get('/rules/new')
        self.assertEqual(rv.status_code, 200)

        data = {
            'msg': 'this is a test message',
            'detection': 'str:DETECTION',
            'mz': 'BODY',
            'custom_mz_val': '',
            'negative': 'checked',
            'score_$SQL': 8,
            'score': '$SQL',
            'rmks': 'this is a test remark',
            'ruleset': 'WEB_APPS'
        }
        rv = self.app.post('/rules/new', data=data, follow_redirects=True)

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()

        self.assertIn(('<li> - OK: created %d : %s</li>' % (_rule.sid, _rule.msg)), rv.data)
        self.assertEqual(_rule.msg, data['msg'])
        self.assertEqual(_rule.detection, data['detection'])
        self.assertEqual(_rule.mz, data['mz'])
        self.assertEqual(_rule.score, data['score'] + ':' + str(data['score_$SQL']))
        self.assertEqual(_rule.rmks, data['rmks'])
        self.assertEqual(_rule.ruleset, data['ruleset'])
        db.session.delete(_rule)
        db.session.commit()

    def test_del_rule(self):
        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()

        db.session.add(NaxsiRules(u'PIF', 'str:test', u'BODY', u'$SQL:8', _rule.sid + 1, u'WEB_APPS',
                                  u'f hqewifueiwf hueiwhf uiewh fiewh fhw', '1', True, 1457101045))
        _sid = _rule.sid + 1
        rv = self.app.get('/rules/del/%d' % _sid)
        self.assertEqual(rv.status_code, 302)

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        self.assertEqual(_rule.sid, _rule.sid)

    def test_plain_rule(self):
        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.get('/rules/plain/%d' % _rule.sid)
        self.assertEqual(rv.status_code, 200)
        rdate = strftime("%F - %H:%M", localtime(float(str(_rule.timestamp))))
        rmks = "# ".join(_rule.rmks.strip().split("\n"))
        expected = """#
# sid: %s | date: %s
#
# %s
#
%s""" % (_rule.sid, rdate, rmks, str(_rule))
        self.assertEqual(expected, rv.data)

    def test_deact_rule(self):
        last_insert = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid

        rv = self.app.get('/rules/deact/%d' % last_insert)  # deactivate
        self.assertEqual(rv.status_code, 200)
        _rule = NaxsiRules.query.filter(NaxsiRules.sid == last_insert).first()
        self.assertEqual(_rule.active, 0)

        rv = self.app.get('/rules/deact/%d' % last_insert)  # activate
        self.assertEqual(rv.status_code, 200)
        _rule = NaxsiRules.query.filter(NaxsiRules.sid == last_insert).first()
        self.assertEqual(_rule.active, 1)

        non_existent_sid = last_insert + 1
        rv = self.app.get('/rules/deact/%d' % non_existent_sid)
        self.assertEqual(rv.status_code, 302)

        rv = self.app.get('/rules/deact/')
        self.assertEqual(rv.status_code, 404)

    def test_search_rule(self):
        rv = self.app.get('/rules/search/')
        self.assertEqual(rv.status_code, 302)

        rv = self.app.get('/rules/search/?s=a')
        self.assertEqual(rv.status_code, 302)

        rv = self.app.get('/rules/search/?s="OR 1=1;--')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('<input type="text" name="s" size="20" value="&#34;OR 1=1;--"', rv.data)
        self.assertIn('<p><strong>Search: OR 11--</strong></p>', rv.data)  # filtered data

        rv = self.app.get('/rules/search/?s=1337')  # get rule by id
        self.assertEqual(rv.status_code, 200)

    def test_edit_rule(self):
        non_existent_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid + 1
        rv = self.app.get('/rules/edit/%d' % non_existent_sid)
        self.assertEqual(rv.status_code, 302)

    def test_parse_rule(self):
        rule_parser = NaxsiRules()
        rv = rule_parser.parse_rule("""MainRule "rx:select|union|update|delete|insert|table|from|ascii|hex|unhex|drop" "msg:sql keywords" "mz:BODY|URL|ARGS|$HEADERS_VAR:Cookie" "s:$SQL:4" id:1000;""")
        self.assertEqual(rv, True)

        self.assertEqual(rule_parser.warnings, ['Cookie in $HEADERS_VAR:Cookie is not lowercase. naxsi is case-insensitive', 'rule IDs below 10k are reserved (1000)'])
        rv = rule_parser.parse_rule("""BasicRule "rx:^ratata$" "mz:$URL:/foobar|$BODY_VAR_X:^tutu$" id:4200001 "s:$SQL:8";""")
        self.assertEqual(rv, False)
        self.assertEqual(rule_parser.error, ["You can't mix static $* with regex $*_X (set(['$BODY_VAR_X', '$URL']))", "parsing of element 'mz:$URL:/foobar|$BODY_VAR_X:^tutu$' failed."])
