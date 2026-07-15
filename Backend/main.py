import json
import os
import re
from pathlib import Path
from typing import Optional
from urllib import error, request

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine
from import_data import import_json_data

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LocalHub 부산 API",
    description="부산 공공데이터와 익명 커뮤니티를 제공하는 FastAPI 서버",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    # 배포 환경에서 DB가 비어 있으면 번들 JSON을 자동 적재합니다.
    db = SessionLocal()
    try:
        count = db.query(models.Location).count()
    finally:
        db.close()

    if count == 0:
        import_json_data()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "LocalHub 부산 API가 정상 실행 중입니다.",
        "docs": "/docs",
    }


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "locations": db.query(models.Location).count(),
        "posts": db.query(models.Post).count(),
    }


@app.get("/api/locations", response_model=list[schemas.LocationResponse])
def get_locations(
    category: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.Location)

    if category:
        query = query.filter(models.Location.category == category)

    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                models.Location.title.like(pattern),
                models.Location.address.like(pattern),
                models.Location.address_detail.like(pattern),
            )
        )

    return (
        query.order_by(models.Location.title.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/api/locations/{location_id}", response_model=schemas.LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    location = (
        db.query(models.Location)
        .filter(models.Location.id == location_id)
        .first()
    )
    if location is None:
        raise HTTPException(status_code=404, detail="지역 정보를 찾을 수 없습니다.")
    return location


@app.get("/api/location-categories")
def get_location_categories(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Location.category,
            func.count(models.Location.id),
        )
        .group_by(models.Location.category)
        .order_by(models.Location.category.asc())
        .all()
    )
    return [{"category": category, "count": count} for category, count in rows]


@app.get("/api/posts", response_model=list[schemas.PostResponse])
def get_posts(
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Post)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                models.Post.title.like(pattern),
                models.Post.content.like(pattern),
            )
        )
    return query.order_by(models.Post.id.desc()).all()


@app.get("/api/posts/{post_id}", response_model=schemas.PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")

    post.views += 1
    db.commit()
    db.refresh(post)
    return post


@app.post("/api/posts", response_model=schemas.PostResponse, status_code=201)
def create_post(data: schemas.PostCreate, db: Session = Depends(get_db)):
    post = models.Post(
        title=data.title.strip(),
        content=data.content.strip(),
        password=data.password,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.put("/api/posts/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: int,
    data: schemas.PostUpdate,
    db: Session = Depends(get_db),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")
    if post.password != data.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")

    post.title = data.title.strip()
    post.content = data.content.strip()
    db.commit()
    db.refresh(post)
    return post


@app.post("/api/posts/{post_id}/verify")
def verify_post_password(
    post_id: int,
    data: schemas.PasswordRequest,
    db: Session = Depends(get_db),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")
    if post.password != data.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    return {"verified": True}


@app.delete("/api/posts/{post_id}")
def delete_post(
    post_id: int,
    data: Optional[schemas.PasswordRequest] = Body(default=None),
    password: Optional[str] = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
):
    password_value = None
    if data is not None:
        password_value = data.password
    elif password is not None:
        password_value = password

    if not password_value:
        raise HTTPException(status_code=422, detail="비밀번호를 입력해 주세요.")

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")
    if post.password != password_value:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")

    db.delete(post)
    db.commit()
    return {"message": "삭제되었습니다."}


def extract_meaningful_keywords(message: str) -> list[str]:
    normalized = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", message)
    tokens = [token.strip() for token in normalized.split() if token.strip()]

    stop_words = {
        "가", "가볼", "가볼만한", "같이", "거기", "그리고", "그냥", "그럼", "그래서",
        "는데", "는", "도", "들", "때", "만", "만한", "면", "좀", "저", "저도",
        "추천", "추천해줘", "해주세요", "해줘", "줘", "좀", "어디", "뭐", "무엇",
        "좋은", "좋아요", "부산", "여행", "가요", "해", "해서", "해서", "이요"
    }

    keywords = []
    for token in tokens:
        cleaned = token.lower()
        if len(cleaned) < 2 or cleaned in stop_words:
            continue
        keywords.append(cleaned)

    return keywords


def get_openai_chat_reply(message: str, db: Session) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    query = db.query(models.Location)
    keywords = extract_meaningful_keywords(message)

    if keywords:
        pattern_terms = [f"%{keyword}%" for keyword in keywords]
        title_filters = [models.Location.title.like(pattern) for pattern in pattern_terms]
        address_filters = [models.Location.address.like(pattern) for pattern in pattern_terms]
        detail_filters = [models.Location.address_detail.like(pattern) for pattern in pattern_terms]
        query = query.filter(
            or_(
                *title_filters,
                *address_filters,
                *detail_filters,
            )
        )

    locations = query.order_by(models.Location.id.asc()).limit(10).all()
    location_context = "\n".join(
        f"- {item.title} ({item.category}, {item.address or '주소 없음'})"
        for item in locations
    )

    prompt = (
        "당신은 부산 여행을 도와주는 친절한 챗봇입니다. "
        "사용자의 질문에 한국어로 짧고 자연스럽게 답하세요. "
        "아래는 DB에 저장된 부산 지역 정보입니다. 이 정보를 참고해서 답변하세요. "
        f"\n\n[DB 위치 정보]\n{location_context}"
    )

    if not locations and keywords:
        prompt += (
            "\n\nDB에 직접 일치하는 장소가 없더라도, 아래 핵심 키워드를 참고해서 "
            "사용자의 의도와 관련된 부산 여행 정보를 자연스럽게 답변하세요. "
            f"\n[핵심 키워드]\n{', '.join(keywords)}"
        )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ],
        "temperature": 0.7,
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
            return content or None
    except (error.HTTPError, error.URLError, KeyError, IndexError, TimeoutError, ValueError):
        return None


@app.post("/api/chat")
def chat(payload: dict, db: Session = Depends(get_db)):
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=400, detail="질문을 입력해 주세요.")

    openai_reply = get_openai_chat_reply(message, db)
    if openai_reply:
        return {"answer": openai_reply}

    category_keywords = {
        "관광": "관광지",
        "명소": "관광지",
        "문화": "문화시설",
        "박물관": "문화시설",
        "레포츠": "레포츠",
        "스포츠": "레포츠",
        "쇼핑": "쇼핑",
        "시장": "쇼핑",
        "숙박": "숙박",
        "호텔": "숙박",
        "여행코스": "여행코스",
        "코스": "여행코스",
        "축제": "축제공연행사",
        "공연": "축제공연행사",
    }

    selected_category = None
    for keyword, category in category_keywords.items():
        if keyword in message:
            selected_category = category
            break

    if "게시글" in message or "커뮤니티" in message:
        posts = db.query(models.Post).order_by(models.Post.id.desc()).limit(3).all()
        if not posts:
            answer = "아직 등록된 커뮤니티 게시글이 없습니다."
        else:
            titles = " / ".join(post.title for post in posts)
            answer = f"최근 커뮤니티 글은 {titles}입니다."
        return {"answer": answer}

    query = db.query(models.Location)
    if selected_category:
        query = query.filter(models.Location.category == selected_category)

    # 사용자가 입력한 전체 문장으로 일치 항목도 먼저 찾아봅니다.
    exact_matches = (
        query.filter(models.Location.title.like(f"%{message}%"))
        .limit(3)
        .all()
    )
    items = exact_matches or query.order_by(models.Location.id.asc()).limit(3).all()

    if not items:
        return {"answer": "조건에 맞는 부산 지역 정보를 찾지 못했습니다."}

    names = ", ".join(item.title for item in items)
    prefix = selected_category or "부산 지역 정보"
    return {"answer": f"{prefix} 추천: {names}"}
