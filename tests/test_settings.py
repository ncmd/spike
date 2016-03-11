try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse

from spike import create_app
from spike.model import db
import unittest

from spike.model.value_templates import ValueTemplates

class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app()
        db.init_app(app)
        app.config['TESTING'] = True

        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_mz(self):
        rv = self.app.get('/settings/mz', follow_redirects=False)
        self.assertEqual(rv.status_code, 200)
        data = rv.data.upper()
        _mz = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_mz").order_by(ValueTemplates.value).all()
        for mz in _mz:
            self.assertIn(mz.value.upper(), data)

    def test_score(self):
        rv = self.app.get('/settings/scores', follow_redirects=False)
        self.assertEqual(rv.status_code, 200)
        data = rv.data.upper()
        _sc = ValueTemplates.query.filter(ValueTemplates.name == "naxsi_score").order_by(ValueTemplates.value).all()
        for sc in _sc:
            self.assertIn(sc.value.upper(), data)
