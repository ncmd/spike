from time import strftime, localtime
import re

from sqlalchemy.orm.exc import UnmappedInstanceError

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

    def tearDown(self):
        pass

    def __create_rule(self):
        """

        :return int: The id of the new rule
        """
        current_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        current_sid = 1337 if current_sid is None else current_sid.sid + 1

        db.session.add(NaxsiRules(u'POUET', 'str:test', u'BODY', u'$SQL:8', current_sid, u'web_server.rules',
                                  u'f hqewifueiwf hueiwhf uiewh fiewh fhw', '1', True, 1457101045))
        self.sid_to_delete = current_sid
        return current_sid

    def __delete_rule(self, sid=None):
        sid = sid  if sid else self.sid_to_delete
        db.session.delete(NaxsiRules.query.filter(sid == NaxsiRules.sid).first())

    def test_index(self):
        rv = self.app.get('/', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('<title>SPIKE! - WAF Rules Builder</title>', rv.data)
        self.assertTrue(re.search(r'<h2>Naxsi - Rules \( \d+ \)</h2>', rv.data) is not None)

    def test_view(self):
        self.__create_rule()

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.get('/rules/view/%d' % _rule.sid)
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/rules/view/%d' % (_rule.sid + 1))
        self.assertEqual(urlparse(rv.location).path, '/rules/')

        self.__delete_rule()

    def test_new_rule(self):
        data = {
            'msg': 'this is a test message',
            'detection': 'DETECTION',
            'mz': 'BODY',
            'custom_mz_val': '',
            'negative': 'checked',
            'score_$SQL': 8,
            'score': '$SQL',
            'rmks': 'this is a test remark',
            'ruleset': 'scanner.rules'
        }
        rv = self.app.post('/rules/new', data=data, follow_redirects=True)
        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()

        self.assertIn(('<li> - OK: created %d : %s</li>' % (_rule.sid, _rule.msg)), rv.data)
        self.assertEqual(_rule.msg, data['msg'])
        self.assertEqual(_rule.detection, 'str:' + data['detection'])
        self.assertEqual(_rule.mz, data['mz'])
        self.assertEqual(_rule.score, data['score'] + ':' + str(data['score_$SQL']))
        self.assertEqual(_rule.rmks, data['rmks'])
        self.assertEqual(_rule.ruleset, data['ruleset'])

        rv = self.app.get('/rules/new')
        self.assertEqual(rv.status_code, 200)

        self.__delete_rule(_rule.sid)

    def test_del_rule(self):
        old_sid = self.__create_rule()

        db.session.add(NaxsiRules(u'POUET', 'str:test', u'BODY', u'$SQL:8', old_sid + 1, u'web_server.rules',
                                  u'f hqewifueiwf hueiwhf uiewh fiewh fhw', '1', True, 1457101045))
        rv = self.app.get('/rules/del/%d' % (old_sid + 1))
        self.assertEqual(rv.status_code, 302)

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        self.assertEqual(_rule.sid, old_sid)

        rv = self.app.get('/rules/del/%d' % (_rule.sid + 1))
        self.assertEqual(rv.status_code, 302)

        self.__delete_rule()

    def test_plain_rule(self):
        self.__create_rule()

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.get('/rules/plain/%d' % _rule.sid)
        self.assertEqual(rv.status_code, 200)
        rdate = strftime("%F - %H:%M", localtime(float(str(_rule.timestamp))))
        rmks = "# ".join(_rule.rmks.strip().split("\n"))
        detect = _rule.detection.lower() if _rule.detection.startswith("str:") else _rule.detection
        negate = 'negative' if _rule.negative == 1 else ''
        expected = """
#
# sid: %s | date: %s
#
# %s
#
MainRule %s "%s" "msg:%s" "mz:%s" "s:%s" id:%s ;

""" % (_rule.sid, rdate, rmks, negate, detect, _rule.msg, _rule.mz, _rule.score, _rule.sid)
        self.assertEqual(expected, rv.data)

        rv = self.app.get('/rules/plain/%d' % (_rule.sid + 1))
        self.assertEqual(rv.status_code, 302)

        self.__delete_rule()

    def test_deact_rule(self):
        rv = self.app.get('/rules/deact/')
        self.assertEqual(rv.status_code, 404)

        last_insert = self.__create_rule()
        non_existent_sid = last_insert + 1

        rv = self.app.get('/rules/deact/%d' % last_insert)  # deactivate
        self.assertEqual(rv.status_code, 200)
        _rule = NaxsiRules.query.filter(NaxsiRules.sid == last_insert).first()
        self.assertEqual(_rule.active, 0)

        rv = self.app.get('/rules/deact/%d' % last_insert)  # activate
        self.assertEqual(rv.status_code, 200)
        _rule = NaxsiRules.query.filter(NaxsiRules.sid == last_insert).first()
        self.assertEqual(_rule.active, 1)

        rv = self.app.get('/rules/deact/%d' % non_existent_sid)
        self.assertEqual(rv.status_code, 302)


        self.__delete_rule()

    def test_search_rule(self):

        self.__create_rule()
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

        self.__delete_rule()

    def test_edit_rule(self):
        non_nxistent_sid = self.__create_rule() + 1
        rv = self.app.get('/rules/edit/%d' % non_nxistent_sid)
        self.assertEqual(rv.status_code, 302)

        self.__delete_rule()
