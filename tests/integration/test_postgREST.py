import unittest
import os
import requests
import json


class TestPostgREST(unittest.TestCase):
    _public_endpoints = ("issue_types", "forecast", "nowcast", "sensor_types", "shading", "weather",
                         "weather_stations")  # "issues",

    def setUp(self):
        url = os.getenv("URL_POSTGREST")
        if not url:
            self.skipTest("No postgREST URL set")
        self.url_postgREST = url

    def _test_url(self, endpoint, min_count=None):
        url = os.path.join(self.url_postgREST, endpoint)

        try:
            res = requests.get(url)
        except Exception:
            res = None

        self.assertIsNotNone(res, f"No connection or response for endpoint {url}")
        self.assertEqual(res.status_code, 200, f"Status code != 200 for endpoint {url}")
        res = json.loads(res.text)
        if min_count is not None:
            self.assertGreaterEqual(len(res), min_count, f"No data for endpoint {url}")
        return res

    def test_endpoints(self):
        for endpoint in self._public_endpoints:
            self._test_url(endpoint=endpoint, min_count=None)

        self._test_url(endpoint="issues", min_count=0)

    def _get_token(self):
        url = os.path.join(self.url_postgREST, "rpc/login")
        passwd = os.getenv("UI_USER_PASSWD")
        if not passwd:
            self.skipTest("No ui user password set")
        data = json.dumps({"username": "qtrees_frontend", "pass": passwd})

        try:
            res = requests.post(url, data, headers={
                "Content-Type": "application/json",
                "accept": "application/json"
            })
        except Exception as e:
            res = None

        return res

    def test_login(self):
        res = self._get_token()
        self.assertIsNotNone(res, f"No connection or response for 'login'")
        self.assertEqual(res.status_code, 200, f"Status code != 200 for 'login'")
        res = json.loads(res.text)

        self.assertTrue("token" in res)
