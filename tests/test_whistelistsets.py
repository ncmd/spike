import unittest

from spike import create_app
from spike.model import db
from time import time
from spike.model.naxsi_whitelistsets import NaxsiWhitelistSets

try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app('../config.cfg')
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

    def test_new(self):
        data = {'wname': 'test_rulset'}
        rv = self.app.post('/whitelistsets/new', data=data, follow_redirects=True)
        self.assertIn('OK created:', str(rv.data))
        rv = self.app.post('/whitelistsets/new', data=data, follow_redirects=True)
        self.assertIn('The whitelist set TEST_RULSET already exists.', str(rv.data))
        _rs = NaxsiWhitelistSets.query.filter('TEST_RULSET' == NaxsiWhitelistSets.name).first()
        db.session.delete(_rs)
        db.session.commit()

    def test_plain(self):
        nwls = NaxsiWhitelistSets('test_rulset', "naxsi-whitelistset: %s" % 'test_rulset', int(time()))
        db.session.add(nwls)
        db.session.commit()

        _rs = NaxsiWhitelistSets.query.filter('test_rulset' == NaxsiWhitelistSets.name).first()

        rv = self.app.get('/whitelistsets/plain/%d' % _rs.id)
        self.assertIn('##########################################################################', str(rv.data))

        db.session.delete(nwls)
        db.session.commit()

    def test_del(self):
        nwls = NaxsiWhitelistSets('test_rset', "naxsi-whitelistset: %s" % 'test_rset', int(time()))
        db.session.add(nwls)
        db.session.commit()

        _rs = NaxsiWhitelistSets.query.filter('test_rset' == NaxsiWhitelistSets.name).first()

        rv = self.app.post('/whitelistsets/del/%d' % _rs.id, follow_redirects=True)
        self.assertIn('Successfully deleted', str(rv.data))

        rv = self.app.post('/whitelistsets/del/%d' % _rs.id, follow_redirects=True)
        self.assertIn("The whitelist set %s doesn&#39;t exist." % _rs.id, str(rv.data))

    def test_select(self):
        nwls = NaxsiWhitelistSets('test_rulset', "naxsi-whitelistset: %s" % 'test_rulset', int(time()))
        db.session.add(nwls)
        db.session.commit()

        _rs = NaxsiWhitelistSets.query.filter('test_rulset' == NaxsiWhitelistSets.name).first()

        rv = self.app.get('/whitelistsets/select/%d' % _rs.id)
        self.assertEqual(200, rv.status_code)

        db.session.delete(nwls)
        db.session.commit()
