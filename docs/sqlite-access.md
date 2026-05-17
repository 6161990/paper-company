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

나가기:

```sql
.quit
```

## One-liners

터미널에서 바로 보기:

```bash
sqlite3 data/paper_company.db "SELECT id, run_date, title FROM briefs ORDER BY run_date DESC;"
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
incident_searches
```

