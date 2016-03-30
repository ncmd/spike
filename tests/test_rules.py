from time import strftime, localtime
import re

from spike.model import db
from spike.model.naxsi_rules import NaxsiRules

from tests import TestsThatNeedsRules

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse


class FlaskrTestCase(TestsThatNeedsRules):
    def test_index(self):
        rv = self.app.get('/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('<title>SPIKE! - WAF Rules Builder</title>', str(rv.data))
        self.assertTrue(re.search(r'<h2>Naxsi - Rules \( \d+ \)</h2>', str(rv.data)) is not None)

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

        self.assertIn(('OK: created %d : %s' % (_rule.sid, _rule.msg)), str(rv.data))
        self.assertEqual(_rule.msg, data['msg'])
        self.assertEqual(_rule.detection, data['detection'])
        self.assertEqual(_rule.mz, data['mz'])
        self.assertEqual(_rule.score, data['score'] + ':' + str(data['score_$SQL']))
        self.assertEqual(_rule.rmks, data['rmks'])
        self.assertEqual(_rule.ruleset, data['ruleset'])
        db.session.delete(_rule)
        db.session.commit()

        # Try to insert an invalid rule
        _sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid
        data['detection'] = 'this string does not start with "str:" or "rx:", sorry'
        rv = self.app.post('/rules/new', data=data)
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(_sid, NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid)

    def test_save_rule(self):
        rv = self.app.get('/rules/save')
        self.assertEqual(rv.status_code, 404)

        data = {
            'msg': 'POUET',
            'detection': 'str:test',
            'mz': 'BODY',
            'custom_mz_val': '',
            'negative': 'checked',
            'score_$SQL': 8,
            'score': '$SQL',
            'rmks': 'f hqewifueiwf hueiwhf uiewh fiewh fhw',
            'ruleset': 'WEB_APPS'
        }
        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.post('/rules/save/{0}'.format(_rule.sid), data=data, follow_redirects=True)

        self.assertIn(data['msg'], str(rv.data))
        self.assertIn(data['detection'], str(rv.data))
        self.assertIn(data['mz'], str(rv.data))
        self.assertIn(data['score'], str(rv.data))
        self.assertIn(data['rmks'], str(rv.data))
        self.assertIn(data['ruleset'], str(rv.data))

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        data['detection'] = 'rx:^lol$'
        rv = self.app.post('/rules/save/{0}'.format(_rule.sid), data=data, follow_redirects=True)
        self.assertIn(data['detection'], str(rv.data))

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        data['detection'] = 'not str: nor rx:'
        rv = self.app.post('/rules/save/{0}'.format(_rule.sid), data=data)
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(urlparse(rv.location).path, '/rules/edit/{}'.format(_rule.sid))

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
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
# sid: {0} | date: {1}
#
# {2}
#
{3}""".format(_rule.sid, rdate, rmks, str(_rule))
        self.assertEqual(expected.encode(), rv.data)

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
        self.assertIn('value="&#34;OR 1=1;--"', str(rv.data))
        self.assertIn('<p><strong>Search: OR 11--</strong></p>', str(rv.data))  # filtered data

        rv = self.app.get('/rules/search/?s=1337')  # get rule by id
        self.assertEqual(rv.status_code, 200)

    def test_edit_rule(self):
        non_existent_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid + 1
        rv = self.app.get('/rules/edit/%d' % non_existent_sid)
        self.assertEqual(rv.status_code, 302)

    def test_parse_rule(self):
        rule_parser = NaxsiRules()

        rv = rule_parser.parse_rule('MainRule "rx:select|union|update|delete|insert|table|from|ascii|hex|unhex|drop"'
                                    '"msg:sql keywords" "mz:BODY|URL|ARGS|$HEADERS_VAR:Cookie" "s:$SQL:4" id:1000;')
        self.assertEqual(rv, True)
        self.assertEqual(rule_parser.warnings,
                         ['Cookie in $HEADERS_VAR:Cookie is not lowercase. naxsi is case-insensitive',
                          'rule IDs below 10k are reserved (1000)'])

        rv = rule_parser.parse_rule('BasicRule "rx:^ratata$" "mz:$URL:/foobar|$BODY_VAR_X:^tutu$"'
                                    'id:4200001 "s:$SQL:8";')
        self.assertEqual(rv, False)
        self.assertIn('$BODY_VAR_X', str(rule_parser.error))
        self.assertIn('$URL', str(rule_parser.error))
        self.assertIn("You can't mix static $* with regex $*_X", str(rule_parser.error))
        self.assertIn("parsing of element 'mz:$URL:/foobar|$BODY_VAR_X:^tutu$' failed.", rule_parser.error)

        rv = rule_parser.parse_rule('"rx:^ratata$" "mz:$URL:/foobar|$BODY_VAR_X:^tutu$"'
                                    'id:4200001 "s:$SQL:8";')
        self.assertEqual(rv, False)
        self.assertIn('No mainrule/basicrule keyword.', rule_parser.error)

        rv = rule_parser.parse_rule('MainRule BasicRule "rx:select"'
                                    '"msg:sql keywords" "mz:BODY|URL|ARGS|$HEADERS_VAR:Cookie" "s:$SQL:4" id:1000;')
        self.assertEqual(rv, False)
        self.assertIn('Multiple mainrule/basicrule keywords.', rule_parser.error)

        rv = rule_parser.parse_rule('MainRule "rx:select"'
                                    '"msg:sql keywords" "mz:BODY" "s:$SQL:4" id:1000 "wrong:LOL";')
        self.assertEqual(rv, False)
        self.assertIn("'wrong:LOL' is an invalid element and thus can not be parsed.", rule_parser.error)

        rv = rule_parser.parse_rule('MainRule "rx:select"'
                                    '"msg:sql keywords" "mz:BODY" "s:$SQL:4" "id:non_numeric";')
        self.assertEqual(rv, False)
        self.assertEqual(['id:non_numeric is not numeric', "parsing of element 'id:non_numeric' failed."],
                         rule_parser.error)

        rv = rule_parser.parse_rule('MainRule "rx:select" "mz:wrong" "msg:sql keywords" "s:$SQL:4" "id:10000";')
        self.assertEqual(rv, False)
        self.assertIn("'wrong' is not a known sub-part of mz : ", str(rule_parser.error))
        self.assertIn("parsing of element 'mz:wrong' failed.", rule_parser.error)
