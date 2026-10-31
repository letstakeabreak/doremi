# round2-kit

Codex와 함께 하는 시간제한 개인 작업 킷. 문제·정답·데이터 없음. MIT.

철학: **읽기 → 사실 확인 → 계획 → 구현 → 같은 명령으로 검증 → 3줄 보고.** 판단은 사람이, 구현은 Codex가, 숫자는 실행 출력이.

## 시험에서 쓰는 법 (2분)

```sh
git clone https://github.com/letstakeabreak/doremi .kit
python3 .kit/tools/envcheck.py
```

Codex 첫 메시지:

```text
.kit/AGENTS.md를 읽고 그대로 따라. 과제 루트는 현재 폴더다.
.kit/templates/*.md를 .kit/ 아래에 복사해 TASK·DECISIONS·VERIFY·HANDOFF를 시작해(이미 있으면 덮어쓰지 마).
README와 과제 안내를 읽고 TASK.md에 사실·가정·열린 질문·완료 조건을 정리한 뒤 계획을 3~6줄로 알려.
```

clone이 막히면 AGENTS.md의 "작업 순서"와 "증거 규칙"만 손으로 타이핑해 `AGENTS.md`로 둔다. 나머지는 없어도 된다.

## 구성

| 경로 | 용도 |
|---|---|
| `AGENTS.md` | Codex 지침. 순서·증거·기록·금지. 짧다. |
| `PLAYBOOK.md` | 사람용. 180분 타임라인, 담당자 질문, 제출 체크, 서술형 뼈대. |
| `RULES.md` | 시험 규정 요약. 당일 아침에 한 번 읽는다. |
| `templates/` | TASK / DECISIONS / VERIFY / HANDOFF 빈 틀. |
| `tools/envcheck.py` | 파이썬·노드·git·pandas·쓰기권한·0.0.0.0 포트 바인딩 점검. 표준 라이브러리만. |
| `tools/csvprofile.py` | CSV 행·열·결측·센티널 후보·중복·수치 범위. 표준 라이브러리만. |
| `tools/stepcount.py` | 단계별 건수 표를 VERIFY.md 형식으로 출력. |
| `tools/serve.py` | 정적 파일·JSON을 0.0.0.0에 띄우는 최소 서버. |
| `tools/submitcheck.py` | 필수 파일 존재·빈 파일·헤더만 있는 CSV·비밀 문자열·미기입 잔재(`__:__`, TODO…)·중복 산출물·`--test-cmd`로 테스트 0개 실행 탐지·git 상태. |
| `skills/` | Codex에 읽힐 짧은 절차: kickoff / verify / handoff / explain. |
| `tests/` | 도구 테스트. `python3 -m unittest discover -s tests` |

도구는 과제 정답을 검증하지 않는다. 업무 검증은 VERIFY.md에 실제 명령과 관찰로 남긴다.

## 하지 않는 것
Codex 설정·홈 디렉터리 변경 없음. 설치 스크립트 없음. 네트워크 사용 없음(serve.py의 로컬 바인딩 제외). 서술형 단계에서는 이 킷을 포함해 어떤 AI도 쓰지 않는다.
