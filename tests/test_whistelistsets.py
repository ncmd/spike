import unittest

from spike import create_app
from spike.model import db
from spike.model.naxsi_whitelist import NaxsiWhitelist

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

    def test_index(self):
        rv = self.app.get('/whitelistsets/')
        self.assertEqual(rv.status_code, 200)

    def test_view(self):
        rv = self.app.get('/whitelistsets/view/')
        self.assertEqual(rv.status_code, 404)

        rv = self.app.get('/whitelistsets/view/1337')
        self.assertEqual(rv.status_code, 200)

