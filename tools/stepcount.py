#!/usr/bin/env python3
"""단계별 건수 표. VERIFY.md에 그대로 붙인다.

사용: python3 stepcount.py 원본=1000 결측제외=980 중복제외=975 최종=975 [--note 결측제외="score 빈칸"]
각 단계의 차이와 비율을 계산해 마크다운 표로 출력. 단계 순서는 입력 순서.
"""
import sys


def table(steps, notes=None):
    notes = notes or {}
    rows = ["| 단계 | 건수 | 직전 대비 | 원본 대비 | 비고 |", "|---|---|---|---|---|"]
    base = steps[0][1] if steps else 0
    prev = None
    for name, n in steps:
        diff = "" if prev is None else f"{n - prev:+d}"
        pct = "" if not base else f"{n / base * 100:.1f}%"
        rows.append(f"| {name} | {n} | {diff} | {pct} | {notes.get(name, '')} |")
        prev = n
    return "\n".join(rows)


def parse(argv):
    steps, notes = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--note":
            k, _, v = argv[i + 1].partition("=")
            notes[k] = v
            i += 2
            continue
        k, _, v = a.partition("=")
        if not v:
            raise SystemExit(f"형식: 이름=정수 (받음: {a})")
        steps.append((k, int(v)))
        i += 1
    return steps, notes


if __name__ == "__main__":
    s, n = parse(sys.argv[1:])
    print(table(s, n))
