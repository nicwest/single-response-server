from dataclasses import dataclass, field
import socket
import webbrowser
import collections
import json
from collections.abc import Mapping


@dataclass
class Headers(Mapping):
    raw: collections.OrderedDict = field(
        default_factory=collections.OrderedDict)
    lower: collections.OrderedDict = field(
        default_factory=collections.OrderedDict)

    def add(self, key, value):
        if key not in self.raw:
            self.raw[key] = []
            self.lower[key.lower()] = []
        self.raw[key].append(value)

    def __getitem__(self, key):
        value = self.lower[key]
        if len(value) == 1:
            return value[0]
        return value

    def __iter__(self, *args, **kwargs):
        return self.raw.__iter__(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        return self.raw.__len__(*args, **kwargs)


@dataclass
class Request:
    method: str
    path: str
    protocol: str
    headers: Headers
    conn: socket.socket
    buf: bytes

    @classmethod
    def read(cls, conn: socket.socket):

        method = None
        path = None
        protocol = None
        headers = Headers()
        headers_read = False
        buf = None

        while not method and not path and not protocol and not headers_read:
            data = conn.recv(1024)

            if not data and not buf:
                break

            if buf:
                data = buf + data
                buf = None

            if not method:
                buf, sep, data = data.partition(b' ')
                if sep is None:
                    break
                method = buf.decode()

            if not path:
                buf, sep, data = data.partition(b' ')
                if sep is None:
                    break
                path = buf.decode()

            if not protocol:
                buff, sep, data = data.partition(b'\r\n')
                if sep is None:
                    break
                protocol = buf.decode()

            while not headers_read:
                buf, sep, data = data.partition(b'\r\n')
                if sep is None:
                    break
                key, _, value = buf.partition(b': ')
                headers.add(key.decode(), value.decode())
                if data == b'\r\n':
                    headers_read = True
                    break

        return cls(
            method=method,
            path=path,
            protocol=protocol,
            headers=headers,
            buf=buf,
            conn=conn,
        )

    def content(self):
        content_length = self.headers.get('content-length')
        if content_length is None:
            return b''
        with self.conn:
            return self.conn.recv(content_length)

    def text(self):
        return self.content().decode()

    def json(self):
        return json.loads(self.text())


RESPONSE = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 50\r\nConnection: close\r\n\r\n<html><body><h1>THANKS BRO</h1></body></html>""".encode()  # noqa


def recieve():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        print(port)
        webbrowser.open(
            f'http://httpbin.org/redirect-to?url=http://localhost:{port}')
        s.listen()
        conn, addr = s.accept()
        r = Request.read(conn)
        conn.sendall(RESPONSE)
        if not r.headers.get('content-length'):
            conn.close()
        print(r.content())


if __name__ == '__main__':
    # send()
    recieve()
