from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        target = self.translate_path(self.path)
        if Path(target).is_file():
            return super().do_GET()

        # Serve the SPA shell for real frontend routes.
        self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    server = ThreadingHTTPServer(("0.0.0.0", 3000), SpaHandler)
    print("Serving DigiSutra web on http://0.0.0.0:3000")
    server.serve_forever()


if __name__ == "__main__":
    main()
