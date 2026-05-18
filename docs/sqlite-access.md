# SQLite Access

Paper Company의 로컬 DB는 여기에 있다.

```text
data/paper_company.db
```

## Open DB

```bash
sqlite3 data/paper_company.db
```

## Useful Commands

테이블 목록:

```sql
.tables
```

스키마 보기:

```sql
.schema briefs
.schema feedback
.schema run_logs
```

저장된 Morning Signal 목록:

```sql
SELECT id, run_date, title, length(content), created_at, updated_at
FROM briefs
ORDER BY run_date DESC;
```

특정 날짜 내용 보기:

```sql
SELECT content
FROM briefs
WHERE run_date = '2026-05-17';
```

브리프별 TOP 5 아이템 보기:

```sql
SELECT b.run_date, i.category, i.title
FROM items i
JOIN briefs b ON b.id = i.brief_id
ORDER BY b.run_date DESC, i.id;
```

최신 브리프의 아이템만 보기:

```sql
SELECT category, title, source
FROM items
WHERE brief_id = (SELECT id FROM briefs ORDER BY run_date DESC LIMIT 1)
ORDER BY id;
```

나가기:

```sql
.quit
```

## One-liners

터미널에서 바로 보기:

```bash
sqlite3 data/paper_company.db "SELECT id, run_date, title FROM briefs ORDER BY run_date DESC;"
```

최신 아이템:

```bash
sqlite3 data/paper_company.db "SELECT category, title FROM items WHERE brief_id = (SELECT id FROM briefs ORDER BY run_date DESC LIMIT 1);"
```

최근 피드백:

```bash
sqlite3 data/paper_company.db "SELECT feedback_type, note, created_at FROM feedback ORDER BY created_at DESC LIMIT 10;"
```

최근 실행 로그:

```bash
sqlite3 data/paper_company.db "SELECT id, trigger_type, status, duration_ms, started_at FROM run_logs ORDER BY started_at DESC LIMIT 10;"
```

테이블 목록:

```bash
sqlite3 data/paper_company.db ".tables"
```

## Current Tables

```text
briefs
items
feedback
mobile_requests
run_logs
```
