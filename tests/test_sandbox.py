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

    def test_sandbox_rule(self):
        rv = self.app.get('/sandbox/rule')
        self.assertEqual(rv.status_code, 200)

    def test_sandbox_visualize(self):
        data = {'rule': 'MainRule "rx:^POUET$" "msg: sqli"  "mz:BODY|URL|ARGS|$HEADERS_VAR:Cookie" "s:$SQL:8" id:1005;',
                'visualise_rule': '1'}
        rv = self.app.post('/sandbox/rule', data=data)
        self.assertEqual(rv.status_code, 302)
        self.assertIn('https://regexper.com/#^POUET$', str(rv.data))

        del data['visualise_rule']
        data['explain_rule'] = 1
        rv = self.app.post('/sandbox/rule', data=data)
        _rule = NaxsiRules('sqli', 'rx:^POUET$', 'BODY|URL|ARGS|$HEADERS_VAR:Cookie', '$SQL:8', '1005', "", "sqli")
        self.assertIn(str(_rule.explain()), str(rv.data).replace('\\', ''))

    def test_explain_rule(self):
        rv = self.app.get('/sandbox/explain_rule/')
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(urlparse(rv.location).path, '/rules/')

        _rule = NaxsiRules.query.order_by(NaxsiRules.sid.desc()).first()
        rv = self.app.get('/sandbox/explain_rule/?rule={0}'.format(_rule.sid + 1), follow_redirects=True)
        self.assertIn('Not rule with id {0}'.format(_rule.sid + 1), str(rv.data))

        rv = self.app.get('/sandbox/explain_rule/?rule={0}'.format(_rule.sid))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(_rule.explain(), str(rv.data))

    def test_explain_nxlog(self):
        rv = self.app.get('/sandbox/explain_nxlog/')
        self.assertEqual(rv.status_code, 405)  # we only accept POST there.

        rv = self.app.post('/sandbox/explain_nxlog/')
        self.assertEqual(rv.status_code, 302)

        rv = self.app.post('/sandbox/explain_nxlog/', data={'nxlog': '1234, lol'})
        self.assertEqual(rv.status_code, 302)

        rv = self.app.post('/sandbox/explain_nxlog/', data={'nxlog': 'ip=1234'})
        self.assertEqual(rv.status_code, 302)

        nxlog = '2013/11/10 07:36:19 [error] 8278#0: *5932 NAXSI_FMT: ip=X.X.X.X&server=Y.Y.Y.Y&'
        nxlog += 'uri=/phpMyAdmin-2.8.2/scripts/setup.php&learning=0&vers=0.52&total_processed=472&total_blocked=204&'
        nxlog += 'block=0&cscore0=$UWA&score0=8&zone0=HEADERS&id0=42000227&var_name0=user-agent, client: X.X.X.X,'
        nxlog += 'server: blog.memze.ro, request: "GET /phpMyAdmin-2.8.2/scripts/setup.php HTTP/1.1", host: "X.X.X.X"'

        rv = self.app.post('/sandbox/explain_nxlog/', data={'nxlog': nxlog})

        self.assertIn('performed a request to', str(rv.data))