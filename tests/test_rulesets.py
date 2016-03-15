from spike.model.naxsi_rules import NaxsiRules
from spike.model.naxsi_rulesets import NaxsiRuleSets

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse

from spike import create_app
from spike.model import db, rulesets_seeds
from time import time
import unittest
import random
import string


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

        rv = self.app.get('/rulesets/', follow_redirects=False)
        self.assertEqual(rv.status_code, 200)

    def test_plain(self):
        rv = self.app.get('/rulesets/plain', follow_redirects=False)
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/rulesets/plain', follow_redirects=True)
        for seed in rulesets_seeds:
            self.assertIn(seed, rv.data)

        rv = self.app.get('/rulesets/plain/1', follow_redirects=True)
        self.assertTrue(any(i for i in rulesets_seeds if i in rv.data))

        rv = self.app.get('/rulesets/plain/123456789', follow_redirects=True)
        self.assertEqual(rv.data, '')

        self.assertTrue(True)

    def test_view(self):
        _rid = NaxsiRuleSets.query.filter().first()
        rv = self.app.get('/rulesets/view/%d' % _rid.id, follow_redirects=False)
        self.assertEqual(rv.status_code, 200)

        _nonexistent_rid = _rid.id + 1
        rv = self.app.get('/rulesets/view/%d' % _nonexistent_rid, follow_redirects=False)
        self.assertEqual(rv.status_code, 200)

    def test_new(self):
        rname = next(iter(rulesets_seeds))
        rv = self.app.post('/rulesets/new', data={'rname': rname})
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(urlparse(rv.location).path, '/rulesets/')

        random_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        rv = self.app.post('/rulesets/new', data={'rname': random_name})
        self.assertEqual(rv.status_code, 302)
        _rule = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == random_name).first()
        self.assertEqual(_rule.name, random_name)
        db.session.delete(_rule)
        db.session.commit()

    def test_del(self):
        random_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        db.session.add(NaxsiRuleSets(random_name, "naxsi-ruleset: %s" % random_name, int(time())))
        db.session.commit()
        _rid = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == random_name).first().id

        _nonexistent_rid = _rid + 1
        rv = self.app.post('/rulesets/del/%d' % _nonexistent_rid)
        self.assertEqual(rv.status_code, 302)

        rv = self.app.post('/rulesets/del/%d' % _rid)
        self.assertEqual(rv.status_code, 302)
        _rule = NaxsiRuleSets.query.filter(NaxsiRuleSets.name == random_name).first()
        self.assertEqual(_rule, None)

    def test_select(self):
        _ruleset = NaxsiRules.query.first().ruleset
        rv = self.app.get('/rulesets/select/%s' % _ruleset)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(_ruleset, rv.data)

        random_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        rv = self.app.get('/rulesets/select/%s' % random_name)
        self.assertEqual(rv.status_code, 200)
