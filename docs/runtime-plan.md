# Runtime Plan

Paper Company는 세 가지 실행 단위로 생각하면 쉽다.

```text
1. Paperclip UI
   항상 켜져 있는 화면

2. n8n
   정해진 시간 또는 Telegram 요청에 일을 시키는 자동화 엔진

3. Claude Agent SDK script
   필요할 때 실행되고 끝나는 탐색 작업자

4. Telegram Bot
   모바일에서 실시간 요청을 보내는 명령창
```

## VPS란?

VPS는 `Virtual Private Server`의 줄임말이다.

쉽게 말하면 인터넷 어딘가에 24시간 켜져 있는 작은 컴퓨터를 빌리는 것이다.

내 Mac에서 n8n을 돌리면 Mac이 꺼지는 순간 자동 실행도 멈춘다. 반면 VPS에 n8n과 Paperclip UI를 올려두면 내 노트북이 꺼져 있어도 오전 7시에 자동 실행된다.

## What Must Stay Running

항상 켜져 있어야 하는 것:

- Paperclip UI
- n8n
- database storage
- Telegram bot webhook

항상 켜져 있을 필요가 없는 것:

- Claude Agent SDK exploration script
- supporting source scripts
- Telegram sending script
- incident search script

Claude Agent SDK는 서버처럼 계속 띄워놓는 대상이 아니다. 보통은 n8n이 필요할 때 Python 스크립트를 실행하고, Claude Agent SDK가 탐색과 큐레이션을 끝낸 뒤 종료된다.

## Local Development Runtime

처음에는 내 Mac에서 이렇게 돌린다.

```text
Mac
  |
  +-- Docker Desktop
        |
        +-- n8n
  |
  +-- Python scripts
  |
  +-- Paperclip UI dev server
```

용도:

- 화면 확인
- n8n 워크플로우 만들기
- Claude Agent SDK exploration 테스트
- 피드백 UI 실험

한계:

- Mac이 꺼지면 오전 7시 자동 실행이 안 된다.

## Production Runtime

실제로 매일 돌릴 때는 VPS에 올린다.

```text
VPS
  |
  +-- Docker Compose
        |
        +-- n8n
        +-- Paperclip UI
        +-- SQLite volume
  |
  +-- Python scripts
        |
        +-- Claude Agent SDK
```

역할:

- n8n은 오전 7시에 workflow 실행
- n8n은 Telegram 요청이 들어오면 실시간 workflow 실행
- Python script는 Claude Agent SDK 탐색 수행
- SQLite는 결과와 피드백 저장
- Paperclip UI는 결과 확인과 피드백 입력 담당

## Does Agent SDK Need To Be Running?

아니다.

Claude Agent SDK는 보통 `상시 실행 서버`가 아니라 `작업 실행 도구`로 보면 된다.

실행 흐름:

```text
07:00
  -> n8n wakes up
  -> n8n runs python scripts/explore_daily.py
  -> explore_daily.py calls Claude Agent SDK
  -> Claude searches, pivots, curates, and returns TOP 5
  -> script saves result
  -> n8n sends Telegram message
  -> script exits
```

단, 나중에 Paperclip UI에서 `다시 랭킹하기`, `이 피드백 반영해서 다시 추천하기` 버튼을 만들면 Paperclip backend가 Claude Agent SDK를 즉시 호출할 수 있다.

그때도 Agent SDK는 계속 떠 있는 게 아니라, 버튼을 누른 순간 실행된다.

## Does Paperclip Need To Be Running?

그렇다.

Paperclip은 피드백 창구이기 때문에 계속 접속 가능해야 한다.

초기에는 내 Mac에서만 실행해도 된다.

실제 운영에서는 VPS에 올려서 항상 켜둔다.

Paperclip이 맡는 일:

- 오늘의 추천 보기
- 추천 이유 보기
- 좋아요/별로예요/저장/실행함 피드백
- 관심사별 내부 Agent 상태 보기
- 실패 로그 보기
- 피드백 기반 재추천 요청

## Recommended Runtime Order

1. 로컬에서 Claude Agent SDK exploration script를 실행한다.
2. 로컬에서 결과 Markdown/JSON을 저장한다.
3. 로컬 n8n에서 script를 실행한다.
4. 로컬 Paperclip UI에서 저장된 결과를 본다.
5. Paperclip UI에서 피드백을 저장한다.
6. exploration prompt가 피드백을 읽게 만든다.
7. VPS에 n8n과 Paperclip UI를 올린다.
8. VPS에서 오전 7시 자동 실행을 켠다.
