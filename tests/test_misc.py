try:
    from urlparse import urlparse
    from StringIO import StringIO
except ImportError:  # python3
    from urllib.parse import urlparse
    from io import StringIO

from spike import create_app
from spike.model import db
import unittest


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app()
        db.init_app(app)
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_robotstxt(self):
        self.assertEqual(self.app.get('/robots.txt').data, b'User-agent: *\n Disallow: /')

    def test_redirect_root(self):
        rv = self.app.get('/', follow_redirects=False)
        self.assertEqual(rv.status_code, 302)
        self.assertEqual(urlparse(rv.location).path, '/rules')

    def test_download_db(self):
        with open('./spike/rules.db', 'rb') as f:
            expected = StringIO(str(f.read()))
        expected.seek(0)
        rv = self.app.get('/download')
        self.assertEqual(str(rv.data), expected.read())

    def test_atom(self):
        rv = self.app.get('/rules.atom')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('<feed xmlns="http://www.w3.org/2005/Atom">', str(rv.data))
