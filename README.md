# Real Estate Listing Collector

부동산 매물 URL을 등록하고, 보수적인 정책으로 수집한 데이터를 Supabase PostgreSQL에 저장한 뒤 엑셀로 내보내는 CLI 기반 MVP입니다.

## 설치

```bash
python -m venv .venv
pip install -r requirements.txt
```

`.env.example`을 참고해 `.env`를 생성합니다.

## 주요 명령

```bash
python -m app.main --help
python -m app.main register-url "https://naver.me/FtoGnVDq"
python -m app.main list-urls
python -m app.main crawl --source-id 1
python -m app.main crawl-url "https://naver.me/FtoGnVDq"
python -m app.main crawl-active
python -m app.main crawl-pending
python -m app.main export --source-id 1
python -m app.main export --all
python -m app.main serve
```

## 로컬 JSON API

```bash
python -m app.main serve --host 127.0.0.1 --port 8000
```

브라우저 또는 HTTP 클라이언트에서 확인합니다.

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/sources
http://127.0.0.1:8000/api/listings
http://127.0.0.1:8000/api/listings?source_id=1
http://127.0.0.1:8000/view
```

Supabase 설정 없이 로컬 파일에만 저장해서 JSON으로 확인:

```bash
curl -X POST http://127.0.0.1:8000/api/crawl-url-local ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://naver.me/FtoGnVDq\",\"memo\":\"로컬 미리보기\"}"

curl http://127.0.0.1:8000/api/listings-local
```

브라우저에서는 `http://127.0.0.1:8000/view`에서 URL을 입력하고 JSON 결과를 바로 확인할 수 있습니다.

Supabase 설정 후 DB에 저장하면서 수집:

```bash
curl -X POST http://127.0.0.1:8000/api/crawl-url ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://naver.me/FtoGnVDq\",\"memo\":\"샘플\"}"

curl http://127.0.0.1:8000/api/listings
```

## DB 생성

Supabase SQL Editor에서 [sql/schema.sql](sql/schema.sql)을 실행합니다.

## 수집 정책

- 병렬 수집 없음
- 요청 간 최소 지연 적용
- HTTP 403, 429 즉시 중단
- 4xx는 재시도하지 않음
- 5xx와 timeout만 제한적으로 재시도
- CAPTCHA, 로그인, 차단 회피, 프록시 우회 미포함

네이버 부동산 수집은 실제 운영 전 robots.txt, 이용약관, 공식 API/제휴 API 가능성을 먼저 확인해야 합니다.
