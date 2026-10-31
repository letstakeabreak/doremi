import io
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import csvprofile  # noqa: E402
import envcheck  # noqa: E402
import stepcount  # noqa: E402
import submitcheck  # noqa: E402


class CsvProfile(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = os.path.join(self.d.name, "a.csv")
        with open(self.p, "w", encoding="utf-8") as f:
            f.write("id,score,grade\n1,10,A\n2,,B\n2,-999,B\n3,30,N/A\n")

    def tearDown(self):
        self.d.cleanup()

    def test_counts(self):
        p = csvprofile.profile(self.p, key="id")
        self.assertEqual(p["rows"], 4)
        self.assertEqual(p["cols"], ["id", "score", "grade"])
        self.assertEqual(p["columns"]["score"]["missing"], 1)
        self.assertEqual(p["columns"]["score"]["sentinel"]["-999"], 1)
        self.assertEqual(p["columns"]["grade"]["sentinel"]["N/A"], 1)
        self.assertEqual(p["dup_keys"], 1)
        self.assertEqual(p["dup_key_rows"], 1)
        self.assertEqual(p["columns"]["score"]["max"], 30.0)

    def test_render_mentions_sentinel(self):
        out = csvprofile.render(csvprofile.profile(self.p, key="id"), "id")
        self.assertIn("sentinel?", out)
        self.assertIn("duplicate_keys=1", out)

    def test_empty(self):
        e = os.path.join(self.d.name, "e.csv")
        open(e, "w").close()
        self.assertEqual(csvprofile.profile(e)["rows"], 0)


class StepCount(unittest.TestCase):
    def test_table(self):
        t = stepcount.table([("원본", 100), ("결측제외", 90), ("최종", 90)], {"결측제외": "빈칸"})
        self.assertIn("| 결측제외 | 90 | -10 | 90.0% | 빈칸 |", t)
        self.assertIn("| 원본 | 100 |  | 100.0% |", t)

    def test_parse(self):
        s, n = stepcount.parse(["a=3", "--note", "a=x", "b=2"])
        self.assertEqual(s, [("a", 3), ("b", 2)])
        self.assertEqual(n, {"a": "x"})

    def test_bad(self):
        with self.assertRaises(SystemExit):
            stepcount.parse(["a"])


class SubmitCheck(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.r = self.d.name
        with open(os.path.join(self.r, "ok.md"), "w") as f:
            f.write("fine\n")
        open(os.path.join(self.r, "empty.csv"), "w").close()

    def tearDown(self):
        self.d.cleanup()

    def test_pass(self):
        ok, res = submitcheck.check(self.r, ["ok.md"])
        self.assertTrue(ok)
        self.assertTrue(any(s == "PASS" and "ok.md" in m for s, m in res))

    def test_missing_and_empty(self):
        ok, res = submitcheck.check(self.r, ["nope.txt", "empty.csv"])
        self.assertFalse(ok)
        self.assertEqual(sum(1 for s, _ in res if s == "FAIL"), 2)

    def test_secret(self):
        with open(os.path.join(self.r, "cfg.py"), "w") as f:
            f.write('API_KEY = "sk-' + "a" * 24 + '"\n')
        ok, res = submitcheck.check(self.r, ["ok.md"])
        self.assertFalse(ok)
        self.assertTrue(any("비밀 의심 cfg.py:1" in m for _, m in res))

    def test_cli_no_artifact(self):
        self.assertEqual(submitcheck.main(["--root", self.r]), 2)

    def test_header_only_csv(self):
        with open(os.path.join(self.r, "h.csv"), "w") as f:
            f.write("id,score\n")
        ok, res = submitcheck.check(self.r, ["h.csv"])
        self.assertFalse(ok)
        self.assertTrue(any("헤더만" in m for _, m in res))

    def test_placeholder_and_stale(self):
        with open(os.path.join(self.r, "TASK.md"), "w") as f:
            f.write("시작: __:__\n")
        open(os.path.join(self.r, "result_v2.csv"), "w").write("a\n1\n")
        _, res = submitcheck.check(self.r, ["ok.md"])
        self.assertTrue(any("미기입 잔재 TASK.md:1" in m for _, m in res))
        self.assertTrue(any("중복 산출물 의심 result_v2.csv" in m for _, m in res))

    def test_parse_test_output(self):
        self.assertEqual(submitcheck.parse_test_output("Ran 5 tests in 0.1s\n\nOK"), (5, True))
        self.assertEqual(submitcheck.parse_test_output("Ran 0 tests in 0.0s\n\nOK"), (0, True))
        self.assertEqual(submitcheck.parse_test_output("Ran 3 tests\n\nFAILED (failures=1)"), (3, False))
        self.assertEqual(submitcheck.parse_test_output("== 4 passed in 0.2s =="), (4, True))
        self.assertIsNone(submitcheck.parse_test_output("nothing"))

    def test_test_cmd_zero(self):
        ok, res = submitcheck.check(self.r, ["ok.md"], test_cmd="echo 'Ran 0 tests'; echo OK")
        self.assertFalse(ok)
        self.assertTrue(any("테스트 0개" in m for _, m in res))

    def test_test_cmd_pass(self):
        ok, res = submitcheck.check(self.r, ["ok.md"], test_cmd="echo 'Ran 2 tests'; echo OK")
        self.assertTrue(ok)
        self.assertTrue(any("테스트 2개 통과" in m for _, m in res))


class EnvCheck(unittest.TestCase):
    def test_bind_free_port(self):
        s = socket.socket()
        s.bind(("0.0.0.0", 0))
        port = s.getsockname()[1]
        s.close()
        self.assertEqual(envcheck.can_bind(port)[0], "OK")

    def test_module(self):
        self.assertEqual(envcheck.module("json")[0], "OK")
        self.assertEqual(envcheck.module("no_such_mod_xyz")[0], "NO")

    def test_main_runs(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = envcheck.main([])
        self.assertEqual(rc, 0)
        self.assertIn("python", buf.getvalue())


class Serve(unittest.TestCase):
    def test_serves_file(self):
        d = tempfile.TemporaryDirectory()
        with open(os.path.join(d.name, "index.html"), "w") as f:
            f.write("<h1>ok</h1>")
        s = socket.socket()
        s.bind(("0.0.0.0", 0))
        port = s.getsockname()[1]
        s.close()
        proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "serve.py"), "--port", str(port), "--dir", d.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            body = None
            for _ in range(50):
                try:
                    body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read()
                    break
                except Exception:  # noqa: BLE001
                    threading.Event().wait(0.1)
            self.assertEqual(body, b"<h1>ok</h1>")
        finally:
            proc.terminate()
            proc.wait(timeout=5)
            proc.stdout.close()
            proc.stderr.close()
            d.cleanup()

    def test_rejects_low_port(self):
        import serve
        self.assertEqual(serve.main(["--port", "80", "--dir", "."]), 2)


if __name__ == "__main__":
    unittest.main()
