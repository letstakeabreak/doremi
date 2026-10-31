#!/usr/bin/env python3
"""환경 점검. 표준 라이브러리만. 설정을 바꾸지 않는다.

사용: python3 envcheck.py [--port 3000]
출력: 항목별 OK / NO / ?  와 값. 종료 코드 0(점검 완료). 판단은 사람이 한다.
"""
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else ""
    except Exception as e:  # noqa: BLE001
        return f"? {type(e).__name__}"


def module(name):
    try:
        m = __import__(name)
        return "OK", getattr(m, "__version__", "")
    except Exception as e:  # noqa: BLE001
        return "NO", type(e).__name__


def can_bind(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", port))
        return "OK", f"0.0.0.0:{port}"
    except OSError as e:
        return "NO", str(e)
    finally:
        s.close()


def can_write(path):
    try:
        with tempfile.NamedTemporaryFile(dir=path, delete=True):
            return "OK", path
    except OSError as e:
        return "NO", str(e)


def main(argv):
    port = 3000
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])
    rows = []
    rows.append(("python", "OK", platform.python_version()))
    rows.append(("cwd", "OK", os.getcwd()))
    rows.append(("write cwd",) + can_write(os.getcwd()))
    for tool in ("node", "npm", "git", "codex", "pip", "pip3"):
        p = shutil.which(tool)
        ver = run([tool, "--version"]) if p else "not on PATH"
        rows.append((tool, "OK" if p and "not found" not in ver and not ver.startswith("?") else "NO", ver))
    for mod in ("pandas", "numpy", "sklearn", "matplotlib", "flask", "fastapi"):
        rows.append((mod,) + module(mod))
    rows.append((f"bind :{port}",) + can_bind(port))
    rows.append(("git repo", "OK" if os.path.isdir(".git") else "NO", "git init 필요" if not os.path.isdir(".git") else run(["git", "rev-parse", "--short", "HEAD"]) or "no commits"))
    try:
        free = shutil.disk_usage(os.getcwd()).free // (1024 * 1024)
        rows.append(("disk free", "OK" if free > 200 else "NO", f"{free} MiB"))
    except OSError:
        rows.append(("disk free", "?", ""))
    w = max(len(r[0]) for r in rows)
    for name, status, val in rows:
        print(f"{name.ljust(w)}  {status:<3} {val}")
    print("\nNO 항목 중 과제에 필요한 것만 대응한다. pandas NO면 csv 모듈로 간다.")
    print("미리보기: 서버는 0.0.0.0, 포트 1024 이상. Vite는 allowedHosts: ['.e2b.app'] 필요.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
