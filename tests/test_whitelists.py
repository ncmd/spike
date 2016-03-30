import unittest
from time import strftime, localtime
import re

from spike import create_app
from spike.model import db
from spike.model.naxsi_whitelist import NaxsiWhitelist

from tests import TestsThatNeedsRules

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
