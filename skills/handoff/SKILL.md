---
name: handoff
description: 단계가 끝날 때 HANDOFF.md를 갱신하고 커밋한다. 새 세션은 이 파일부터 읽는다.
---

1. HANDOFF.md를 덮어쓴다: 현재 단계 / 된 것(파일·명령·커밋) / 안 된 것 / 다음 한 가지 / 건드리지 말 것.
2. TASK.md의 상태 열과 "다음 할 일"을 맞춘다.
3. `git add -A && git commit -m "[단계] 무엇: 왜"`. push 금지.
4. "새 세션에서 `.kit/HANDOFF.md`와 `.kit/TASK.md`를 읽고 이어서"라고 응시자에게 한 줄 알린다.
