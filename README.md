# LocalHub 부산 완성 프로젝트

실제 부산 TourAPI JSON 7개를 SQLite에 적재하고, Vue 3 CDN 기반 HTML UI와 FastAPI를 연결한 프로젝트입니다.

## 포함 데이터

- 관광지: 351건
- 문화시설: 123건
- 레포츠: 65건
- 쇼핑: 986건
- 숙박: 140건
- 여행코스: 22건
- 축제공연행사: 72건
- 총 적재: 1759건

## 실행 방법

### 1. 백엔드 실행

Git Bash:

```bash
cd Backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload
```

Swagger:
- http://127.0.0.1:8000/docs

### 2. 프론트 실행

VS Code에서 `Front/index.html`을 열고 Live Server로 실행합니다.

예:
- http://127.0.0.1:5500/Front/index.html

## 주요 기능

- 실제 부산 공공데이터 카테고리별 조회
- 대표 이미지, 주소 표시
- SQLite 기반 게시글 CRUD
- 게시글 검색 및 조회수
- 수정/삭제 비밀번호 검증
- 간단한 지역정보 챗봇 API
- 데이터 출처 및 라이선스 표시

## 주의

프론트는 기본적으로 `http://127.0.0.1:8000`의 백엔드에 연결합니다.
Render 배포 후에는 `Front/index.html`의 `API_BASE_URL`을 Render URL로 변경하세요.
