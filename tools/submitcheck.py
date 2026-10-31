#!/usr/bin/env python3
"""제출 전 점검. 파일 존재·빈 파일·비밀 문자열·미기입 잔재·중복 산출물·테스트 실행 수·git 상태. 표준 라이브러리만. 파일을 바꾸지 않는다.

사용: python3 submitcheck.py --artifact out/result.csv --artifact DECISIONS.md [--root .] [--test-cmd "python3 -m unittest discover -s tests"]
종료 코드: 0 전부 통과 / 1 실패 있음 / 2 artifact 미지정.
통과해도 업무 정답·테스트 통과·제출 완료를 뜻하지 않는다.
"""
import argparse
import os
import re
import subprocess
import sys

SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9_-]{16,}", "OpenAI 형식 키"),
    (r"AKIA[0-9A-Z]{16}", "AWS 키"),
    (r"ghp_[A-Za-z0-9]{20,}", "GitHub 토큰"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", "키=값 패턴"),
    (r"\b\d{6}-[1-4]\d{6}\b", "주민등록번호 형식"),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".kit"}
TEXT_EXT = {".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".env", ".csv", ".html", ".sh", ".cfg", ".ini"}


PLACEHOLDERS = ["__:__", "NOT_STARTED", "NO_DECISIONS_RECORDED", "TODO", "TBD", "미정", "확인 필요", "결정 대기", "<여기에", "<URL>", "<해시>", "<본인 이름>"]
DOC_EXT = {".md", ".txt"}


def scan_placeholders(root):
    hits = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS - {".kit"}]
        for f in fn:
            p = os.path.join(dp, f)
            if os.path.splitext(f)[1] not in DOC_EXT or "templates" in dp.split(os.sep):
                continue
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        for ph in PLACEHOLDERS:
                            if ph in line:
                                hits.append((os.path.relpath(p, root), i, ph))
                                break
            except OSError:
                continue
    return hits


def scan_stale_outputs(root):
    pat = re.compile(r"(_v\d+|_old|_backup|\(\d+\)|_copy)\.[A-Za-z0-9]+$")
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        out += [os.path.relpath(os.path.join(dp, f), root) for f in fn if pat.search(f)]
    return out


def parse_test_output(text):
    """unittest 'Ran N tests' / pytest 'N passed' 에서 실행 수를 뽑는다. 못 찾으면 None."""
    m = re.search(r"Ran (\d+) tests?", text)
    if m:
        n = int(m.group(1))
        return n, ("FAILED" not in text and "Error" not in text)
    m = re.search(r"(\d+) passed", text)
    if m:
        return int(m.group(1)), "failed" not in text.split(m.group(0))[1][:60]
    if re.search(r"no tests ran|collected 0 items", text):
        return 0, False
    return None


def scan_secrets(root):
    hits = []
    scanned = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = os.path.join(dp, f)
            if os.path.splitext(f)[1] not in TEXT_EXT or os.path.getsize(p) > 2_000_000:
                continue
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    scanned += 1
                    for i, line in enumerate(fh, 1):
                        for pat, label in SECRET_PATTERNS:
                            if re.search(pat, line):
                                hits.append((os.path.relpath(p, root), i, label))
                                break
            except OSError:
                continue
    return hits, scanned


def git_status(root):
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return None
        return out.stdout.strip().splitlines()
    except Exception:  # noqa: BLE001
        return None


def line_count(p, limit=3):
    n = 0
    with open(p, "rb") as fh:
        for _ in fh:
            n += 1
            if n >= limit:
                break
    return n


def check(root, artifacts, test_cmd=None):
    results = []
    ok = True
    for a in artifacts:
        p = os.path.join(root, a)
        if not os.path.isfile(p):
            results.append(("FAIL", f"{a}: 없음"))
            ok = False
        elif os.path.getsize(p) == 0:
            results.append(("FAIL", f"{a}: 빈 파일"))
            ok = False
        elif a.lower().endswith((".csv", ".tsv", ".jsonl")) and line_count(p, 2) < 2:
            results.append(("FAIL", f"{a}: 헤더만 있고 데이터 행 없음"))
            ok = False
        else:
            results.append(("PASS", f"{a}: {os.path.getsize(p)} bytes"))
    hits, scanned = scan_secrets(root)
    if hits:
        ok = False
        for f, i, label in hits[:20]:
            results.append(("FAIL", f"비밀 의심 {f}:{i} ({label})"))
    elif scanned == 0:
        results.append(("NOT_RUN", "비밀 스캔 대상 파일 0개"))
    else:
        results.append(("PASS", f"비밀 문자열 없음 ({scanned}개 파일)"))
    for f, i, ph in scan_placeholders(root)[:20]:
        results.append(("WARN", f"미기입 잔재 {f}:{i} '{ph}'"))
    for f in scan_stale_outputs(root)[:10]:
        results.append(("WARN", f"중복 산출물 의심 {f}"))
    if test_cmd:
        try:
            out = subprocess.run(test_cmd, cwd=root, shell=True, capture_output=True, text=True, timeout=300)
            parsed = parse_test_output(out.stdout + out.stderr)
            if parsed is None:
                results.append(("WARN", f"테스트 출력에서 실행 수를 못 읽음 (exit {out.returncode})"))
            elif parsed[0] == 0:
                ok = False
                results.append(("FAIL", "테스트 0개 실행 — 초록불 아님"))
            elif not parsed[1] or out.returncode != 0:
                ok = False
                results.append(("FAIL", f"테스트 실패 (실행 {parsed[0]}개, exit {out.returncode})"))
            else:
                results.append(("PASS", f"테스트 {parsed[0]}개 통과"))
        except subprocess.TimeoutExpired:
            ok = False
            results.append(("FAIL", "테스트 300초 초과"))
    st = git_status(root)
    if st is None:
        results.append(("WARN", "git 저장소 아님 또는 git 없음"))
    elif st:
        results.append(("WARN", f"커밋 안 된 변경 {len(st)}건: " + ", ".join(s[3:] for s in st[:5])))
    else:
        results.append(("PASS", "git 깨끗"))
    return ok, results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--artifact", action="append", default=[])
    ap.add_argument("--test-cmd", help='예: "python3 -m unittest discover -s tests"')
    a = ap.parse_args(argv)
    if not a.artifact:
        print("--artifact 로 필수 제출 파일을 지정한다. (README의 파일명 그대로)")
        return 2
    ok, results = check(os.path.abspath(a.root), a.artifact, a.test_cmd)
    for s, msg in results:
        print(f"{s:<5}{msg}")
    print("\n통과는 파일 기본 검사일 뿐이다. 실행 명령 재실행·탭 저장됨·README 파일명 대조는 직접 한다.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
