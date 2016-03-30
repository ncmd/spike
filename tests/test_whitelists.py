import unittest

from spike import create_app
from spike.model import db

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app()
        db.init_app(app)
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.created_rules = list()

    def tearDown(self):
        pass

    def test_index(self):
        rv = self.app.get('/whitelists/')

    def test_new(self):
        rv = self.app.get('/whitelists/new')
        self.assertEqual(rv.status_code, 200)

    def test_generate(self):
        rv = self.app.get('/whitelists/generate')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.post('/whitelists/generate')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Please input nxlogs', str(rv.data))

        rv = self.app.post('/whitelists/generate', data={'nxlogs': 'pouet,lol'})
        self.assertEqual(rv.status_code, 200)
        self.assertIn('string &#34;ip=&#34; not found.', str(rv.data))

        rv = self.app.post('/whitelists/generate', data={'nxlogs': 'ip=1234'})
        self.assertEqual(rv.status_code, 200)
        self.assertIn('string &#34;,&#34; not found.', str(rv.data))

        logs = "2013/11/10 07:36:19 [error] 8278#0: *5932 NAXSI_FMT: ip=X.X.X.X&server=Y.Y.Y.Y&"\
                "uri=/phpMyAdmin-2.8.2/scripts/setup.php&learning=0&vers=0.52&total_processed=472&total_blocked=204&"\
                "block=0&cscore0=$UWA&score0=8&zone0=HEADERS&id0=42000227&var_name0=user-agent, client: X.X.X.X,"\
                'server: blog.memze.ro, request: "GET /phpMyAdmin-2.8.2/scripts/setup.php HTTP/1.1", host: "X.X.X.X"'
        rv = self.app.post('/whitelists/generate', data={'nxlogs': logs})
        self.assertEqual(rv.status_code, 200)
        self.assertIn('BasicRule wl:42000227 "mz:user-agent:HEADERS"', str(rv.data))
