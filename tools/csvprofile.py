#!/usr/bin/env python3
"""CSV 첫인상. 표준 라이브러리만. 파일을 바꾸지 않는다.

사용: python3 csvprofile.py data.csv [--key ID] [--max-rows 200000] [--delim ,]
출력: 행·열, 컬럼별 결측·고유값·수치 범위·센티널 후보, --key 중복 건수.
"""
import argparse
import csv
import sys
from collections import Counter

SENTINELS = {"", "NA", "N/A", "NULL", "null", "None", "nan", "NaN", "-", "?", "-999", "-9999", "9999", "99999", "-1"}


def to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def profile(path, key=None, max_rows=200000, delim=","):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=delim)
        header = next(reader, None)
        if header is None:
            return {"rows": 0, "cols": [], "columns": {}, "truncated": False}
        cols = {h: {"missing": 0, "values": Counter(), "min": None, "max": None, "numeric": 0, "sentinel": Counter()} for h in header}
        rows = 0
        keys = Counter()
        truncated = False
        for row in reader:
            rows += 1
            if rows > max_rows:
                truncated = True
                break
            for h, v in zip(header, row):
                c = cols[h]
                v = v.strip()
                if v in SENTINELS:
                    c["sentinel"][v or "<blank>"] += 1
                    if v == "":
                        c["missing"] += 1
                if len(c["values"]) < 50:
                    c["values"][v] += 1
                x = to_float(v)
                if x is not None:
                    c["numeric"] += 1
                    c["min"] = x if c["min"] is None else min(c["min"], x)
                    c["max"] = x if c["max"] is None else max(c["max"], x)
            if key and key in header:
                keys[row[header.index(key)].strip()] += 1
        dup = sum(n - 1 for n in keys.values() if n > 1) if key else None
        return {"rows": rows if not truncated else max_rows, "cols": header, "columns": cols, "truncated": truncated, "dup_key_rows": dup, "dup_keys": len([k for k, n in keys.items() if n > 1]) if key else None}


def render(p, key=None):
    out = [f"rows={p['rows']}{' (truncated)' if p['truncated'] else ''} cols={len(p['cols'])}"]
    if key:
        out.append(f"key={key} duplicate_keys={p['dup_keys']} extra_rows={p['dup_key_rows']}")
    out.append(f"{'column':<24}{'numeric':>8}{'blank':>7}{'sentinel':>10}  range / sample")
    for h in p["cols"]:
        c = p["columns"][h]
        sent = sum(c["sentinel"].values()) - c["missing"]
        if c["numeric"] and c["numeric"] >= max(1, p["rows"] - c["missing"]) * 0.9:
            detail = f"[{c['min']:g}, {c['max']:g}]"
        else:
            sample = ", ".join(f"{k or '<blank>'}×{n}" for k, n in c["values"].most_common(3))
            detail = f"uniq≥{len(c['values'])}: {sample}"
        flag = " <- sentinel? " + ",".join(k for k in c["sentinel"] if k != "<blank>") if sent else ""
        out.append(f"{h[:23]:<24}{c['numeric']:>8}{c['missing']:>7}{sent:>10}  {detail}{flag}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--key")
    ap.add_argument("--max-rows", type=int, default=200000)
    ap.add_argument("--delim", default=",")
    a = ap.parse_args(argv)
    print(render(profile(a.path, a.key, a.max_rows, a.delim), a.key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
