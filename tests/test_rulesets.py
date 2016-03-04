from time import strftime, localtime

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse

from spike import create_app, seeds
from spike.model import db
import unittest


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app('../config.cfg')
        db.init_app(app)
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_index(self):
        rv = self.app.get('/rulesets', follow_redirects=False)
        self.assertEqual(rv.status_code, 301)
        self.assertEqual(urlparse(rv.location).path, '/rulesets/')

    def test_plain(self):
        rv = self.app.get('/rulesets/plain', follow_redirects=False)
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/rulesets/plain', follow_redirects=True)
        for seed in seeds.rulesets_seeds:
            self.assertIn(seed, rv.data)