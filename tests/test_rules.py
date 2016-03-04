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

    def test_del_rule(self):
        current_sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid
        self.test_add_rule()

        sid = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first().sid
        rv = self.app.get('/rules/del/%d' % sid)
        assert rv.status_code == 302

        rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()

        assert rule.sid == current_sid



if __name__ == '__main__':
    unittest.main()