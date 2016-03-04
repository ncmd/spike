try:
    from urlparse import urlparse
except ImportError:  # python3
    from urllib.parse import urlparse

from spike import create_app
from spike.model import db
import unittest


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app()
        db.init_app(app)
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_index(self):
        rv = self.app.get('/docs', follow_redirects=True)
        self.assertIn('<h2>Spike - Docs - Overview</h2>', rv.data)

    def test_readme(self):
        rv = self.app.get('/docs/README.md', follow_redirects=True)
        self.assertIn('Spike is a simple web application to manage', rv.data)

    def test_dynamic_doc(self):
        rv = self.app.get('/docs/docs.md', follow_redirects=True)
        self.assertIn('<h2><a href="/docs">Spike - Docs</a></h2>', rv.data)

    def test_LFI(self):
        rv = self.app.get('/docs/../../../../etc/passwd', follow_redirects=True)
        self.assertIn('<h2>Spike - Docs - Overview</h2>', rv.data)
        self.assertNotIn('root:x:0:0:root:/root:', rv.data)
