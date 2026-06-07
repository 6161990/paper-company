# Feedback Loop

Paper Company의 핵심은 피드백이다.

좋은 자동화는 한 번에 완성되지 않는다. 매일 추천을 받고, 내가 반응하고, 그 반응이 다음 추천에 들어가야 내 입맛에 맞아진다.

## Feedback Channel

피드백 창구는 두 단계로 간다.

초기에는 Telegram에서 `/save`, `/feedback`으로 바로 받는다.
Paperclip UI가 생기면 카드별 버튼 피드백을 주 창구로 옮긴다.

이유:

- Telegram은 지금 바로 모바일에서 피드백을 남기기 쉽다.
- Telegram 텍스트만으로는 카드별 정밀 피드백을 받기 어렵다.
- Paperclip은 추천 이유, 원본 링크, Agent 로그를 함께 보여줄 수 있다.
- 내가 왜 좋았는지/싫었는지 남기기 좋다.

## Feedback Types

처음 필요한 피드백:

```text
save
  다시 보고 싶다

like
  내 취향에 맞다

dislike
  내 취향이 아니다

acted_on
  실제로 뭔가 해봤다

make_content
  글/영상/프로젝트 소재로 쓰고 싶다

hide_source
  이 출처는 별로다

more_like_this
  이런 방향을 더 받고 싶다
```

## Feedback UI

추천 카드 하나는 이렇게 생긴다.

```text
┌──────────────────────────────────────────┐
│ Claude Agent SDK로 개인 리서치 에이전트 만들기 │
├──────────────────────────────────────────┤
│ 왜 지금: 로컬 자동화 실험에 바로 연결됨        │
│ 왜 나에게 맞나: n8n + Agent 구조와 맞물림     │
│ 다음 행동: exploration prompt를 30분 안에 만든다 │
├──────────────────────────────────────────┤
│ [Save] [Like] [Dislike] [Acted] [More]    │
└──────────────────────────────────────────┘
```

## Feedback Storage

초기에는 SQLite에 저장한다.

테이블 초안:

```text
briefs
  id
  run_date
  title
  created_at

items
  id
  brief_id
  title
  source
  url
  category
  why_now
  why_fit
  next_action
  expansion
  score

feedback
  id
  item_id
  brief_id
  feedback_type
  note
  created_at
```

## How Feedback Changes Recommendations

다음 날 exploration prompt에 최근 피드백을 넣는다.

예시:

```text
Recent user feedback:

- liked: Claude Agent SDK 실전 예제
  reason: 바로 내 프로젝트에 붙일 수 있어서 좋았음

- disliked: 추상적인 AI 미래 전망 글
  reason: 너무 멀고 오늘 할 행동이 없음

- acted_on: n8n Schedule Trigger 실험
  reason: 살아 움직이는 시스템 느낌이 좋았음

Use this feedback to rank today's candidates.
Prefer concrete, buildable, project-shaped items.
Avoid abstract trend commentary without a 30-minute action.
```

## Real-Time Feedback

실시간 피드백은 두 단계로 간다.

### Step 1: Store Immediately

Telegram 또는 Paperclip에서 피드백을 주면 즉시 SQLite에 저장한다.

```text
send /feedback 오늘 주식/비즈니스 개념 좋았어
  -> SQLite feedback insert
  -> paper_company/recent_feedback.json refresh

click Like
  -> POST /feedback
  -> SQLite insert
  -> UI updates card state
```

현재 Paperclip MVP에서는 카드별 피드백 상태가 보인다.

```text
Save 1
Like 2
No feedback yet
```

이미 누른 피드백 타입은 카드 버튼이 활성 상태로 표시된다.

### Step 2: Re-rank On Demand

나중에는 `Re-rank with my feedback` 버튼을 둔다.

```text
click Re-rank
  -> Paperclip backend loads today's candidates
  -> backend loads recent feedback
  -> Claude Agent SDK runs again
  -> new curation appears in UI
```

이 기능이 있으면 매일 아침 받은 결과가 별로여도, 그 자리에서 피드백을 주고 다시 맞출 수 있다.

## Feedback Priority

가장 강한 신호:

1. `acted_on`
2. `make_content`
3. `more_like_this`
4. `like`
5. `save`
6. `dislike`
7. `hide_source`

`acted_on`은 가장 중요하다. 실제 행동으로 이어진 아이템이 Paper Company의 핵심 성공 지표다.
