"""Run with python -m unittest discover -s apps/web/tests -p '*_test.py'."""
import importlib.util
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location("web_server", Path(__file__).parents[1] / "server.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DeepLinkTests(unittest.TestCase):
    def test_nested_routes_keep_root_assets_and_missing_assets_are_404(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), module.SpaHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            for path in ["/products/product::1", "/seller/products/new", "/admin/seller-applications"]:
                with urlopen(origin + path) as response:
                    html = response.read().decode()
                    self.assertIn('src="/src/app.js"', html)
                    self.assertIn('href="/indigo-cloud.css"', html)
            with urlopen(origin + "/src/app.js") as response:
                self.assertIn("javascript", response.headers["Content-Type"])
            with self.assertRaises(HTTPError) as error:
                urlopen(origin + "/seller/src/missing.js")
            self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
