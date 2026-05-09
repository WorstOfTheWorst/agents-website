import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
COMFY_IP_PATH = os.path.join(DATA_DIR, 'comfy_ip.json')

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/save_comfy_ip':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = json.loads(body)
                url = data.get('url')
                if not url:
                    raise ValueError('Missing url')
                # Ensure data directory exists
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(COMFY_IP_PATH, 'w', encoding='utf-8') as f:
                    json.dump({'url': url}, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Saved')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f'Error: {e}'.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

    # Ensure MIME types for common files are served correctly
    def guess_type(self, path):
        return super().guess_type(path)

def run(port: int = 8000):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, Handler)
    print(f'Serving on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    import sys
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(p)
