#!/usr/bin/env python3
"""정적 파일 서버. 0.0.0.0 바인딩. 표준 라이브러리만.

사용: python3 serve.py --port 3000 --dir out
Browser 패널에 PORT=3000, 경로=/ 입력. 이 터미널 탭은 닫지 않는다. Ctrl+C로 종료.
JSON·CSV·HTML을 그대로 서빙한다. 간단한 화면은 out/index.html 하나로 충분하다.
"""
import argparse
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".csv": "text/csv; charset=utf-8", ".json": "application/json", ".md": "text/plain; charset=utf-8"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=3000)
    ap.add_argument("--dir", default=".")
    a = ap.parse_args(argv)
    if a.port < 1024:
        print("포트는 1024 이상을 쓴다.", file=sys.stderr)
        return 2
    d = os.path.abspath(a.dir)
    if not os.path.isdir(d):
        print(f"폴더 없음: {d}", file=sys.stderr)
        return 2
    srv = ThreadingHTTPServer(("0.0.0.0", a.port), partial(Handler, directory=d))
    print(f"serving {d} on 0.0.0.0:{a.port}  (Browser 패널: PORT {a.port}, 경로 /)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
