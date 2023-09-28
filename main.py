from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime
import urllib.parse
import mimetypes
import pathlib
import socket
import json

HTTP_PORT = 3000
UDP_PORT = 5000
STORAGE = "storage/data.json"


class main:
    udp_port = UDP_PORT
    def __init__(
        self,
        http_port: int = HTTP_PORT,
        udp_port: int = UDP_PORT,
        storage: str = STORAGE
    ):
        main.udp_port = udp_port
        self.setup_http(http_port)
        self.setup_udp(storage)

    def setup_http(self, http_port: int):
        self.server_address = ('', http_port)
        self.http_server = HTTPServer(self.server_address, HttpHandler)
        self.http_thread = Thread(target=self.http_server.serve_forever)
        self.killerthread = Thread(target=self.http_server.shutdown)

    def setup_udp(self, storage: str):
        self.udp_server = socket.gethostname(), main.udp_port
        self.storage = pathlib.Path().joinpath(storage)
        if not self.storage.is_file():
            self.storage.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage, "w", encoding='utf-8') as f:
                f.write("{}")

    def loop(self):
        self.http_thread.start()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(self.udp_server)
            sock.settimeout(0.1)
            try:
                while True:
                    try:
                        data, address = sock.recvfrom(1024)
                        print(f"Received: {data.decode()} from: {address}")
                        self.append_to_file(data)
                    except TimeoutError:
                        pass
            except KeyboardInterrupt:
                self.killerthread.start()
                print("Servers are going down")
                exit(1)

    def append_to_file(self, data):
        with open(self.storage, "r", encoding='utf-8') as f:
            try:
                data_dict = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f"Error! Could not read '{self.storage}'.")
                data_dict = {}
        data_parse = urllib.parse.unquote_plus(data.decode()).split('&')
        new_data = {k: v for k, v in [x.split('=') for x in data_parse]}
        data_dict |= {str(datetime.now()): new_data}
        with open(self.storage, "w", encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.send_udp(data)
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_udp(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            server = socket.gethostname(), main.udp_port
            sock.sendto(data, server)

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


if __name__ == '__main__':
    m = main()
    m.loop()
