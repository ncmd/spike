from time import strftime, localtime

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse

import re

from spike import create_app
from spike.model import db
from spike.model.naxsi_rules import ValueTemplates, NaxsiRules, NaxsiRuleSets
import unittest


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        app = create_app()
        db.init_app(app)
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_robotstxt(self):
        assert self.app.get('/robots.txt').data == 'User-agent: *\n Disallow: /'

    def test_redirect_root(self):
        rv = self.app.get('/', follow_redirects=False)
        assert rv.status_code == 302
        assert urlparse(rv.location).path == '/rules'

    def test_add_rule(self):
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
        rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()

        assert ('<li> - OK: created %d : %s</li>' % (rule.sid, rule.msg)) in rv.data
        assert rule.msg == data['msg']
        assert rule.detection == 'str:' + data['detection']
        assert rule.mz == data['mz']
        assert rule.score == data['score'] + ':' + str(data['score_$SQL'])
        assert rule.rmks == data['rmks']
        assert rule.ruleset == data['ruleset']

        _rule = NaxsiRules.query.filter(rule.sid == NaxsiRules.sid).first()
        db.session.delete(_rule)

    def test_del_rule(self):
        current_sid = int(NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid)
        db.session.add(NaxsiRules(u'POUET', 'str:OIJEFOJEWFOIJEWF', u'BODY', u'$SQL:8', current_sid+1, u'web_server.rules',
         u'f hqewifueiwf hueiwhf uiewh fiewh fhw', '1', True, 1457101045))

        sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid
        rv = self.app.get('/rules/del/%d' % sid)
        assert rv.status_code == 302

        rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        assert rule.sid == current_sid

    def test_plain_rule(self):
        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.get('/rules/plain/%d' % _rule.sid)
        assert rv.status_code == 200
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
        assert expected == rv.data
        _rule = NaxsiRules.query.filter(_rule.sid == NaxsiRules.sid).first()
        db.session.delete(_rule)


if __name__ == '__main__':
    unittest.main()