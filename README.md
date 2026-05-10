# Paper Company

영감 기반 AI 콘텐츠 공장 + 관제실입니다.

목적은 콘텐츠 자동 생산보다 먼저, AI가 매일 나 대신 세상을 둘러보고 나에게 꽂힐 가능성이 높은 아이템을 가져오게 하는 것입니다.

오늘 목표는 작게 갑니다.

1. n8n을 로컬에서 실행한다.
2. 브라우저에서 n8n 화면을 본다.
3. 이후 `매일 오전 7시 영감 탐색` 워크플로우를 하나씩 붙인다.

## Run

```bash
cp .env.example .env
docker compose up -d
```

n8n:

```text
http://localhost:5678
```

## Stop

```bash
docker compose down
```

## MVP Direction

- Local Runtime: 하나의 Claude Agent SDK 실행
- Internal Agents: AI, Backend, Money, Inspiring People
- 역할: 관심사별 탐색, 방향 전환, 큐레이션, TOP 5 추천

## Product Notes

- [Vision](docs/vision.md)
- [Roadmap](docs/roadmap.md)
- [Runtime Plan](docs/runtime-plan.md)
- [Feedback Loop](docs/feedback-loop.md)
- [Telegram Interface](docs/telegram-interface.md)
- [Output Experience](docs/output-experience.md)
- [Agent Map](docs/agent-map.md)
- [Daily Brief Format](docs/daily-brief-format.md)
