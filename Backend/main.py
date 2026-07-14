from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_posts(db: Session) -> None:
    if db.query(models.Post).count() > 0:
        return

    samples = [
        models.Post(
            title="서울 경복궁 야간개장 예매 팁을 공유합니다.",
            content="모바일 본인인증을 미리 완료하고 예매 시작 전에 접속하면 조금 더 수월합니다.",
            password="1234",
        ),
        models.Post(
            title="여의도 한강공원 배달존 위치가 궁금합니다.",
            content="여의나루역에서 한강공원 방향으로 이동하면 배달존 안내 표지판을 확인할 수 있습니다.",
            password="1111",
        ),
    ]
    db.add_all(samples)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_posts(db)
    finally:
        db.close()
    yield


app = FastAPI(title="LocalHub API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "LocalHub backend running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/posts", response_model=list[schemas.PostResponse])
def get_posts(
    keyword: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Post)
    if keyword and keyword.strip():
        search = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                models.Post.title.ilike(search),
                models.Post.content.ilike(search),
            )
        )
    return query.order_by(models.Post.id.desc()).all()


@app.get("/api/posts/{post_id}", response_model=schemas.PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")

    post.view_count += 1
    db.commit()
    db.refresh(post)
    return post


@app.post(
    "/api/posts",
    response_model=schemas.PostResponse,
    status_code=status.HTTP_201_CREATED,
)
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


@app.delete("/api/posts/{post_id}")
def delete_post(
    post_id: int,
    data: schemas.PasswordRequest,
    db: Session = Depends(get_db),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")
    if post.password != data.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")

    db.delete(post)
    db.commit()
    return {"message": "게시글이 삭제되었습니다."}


@app.post("/api/chat", response_model=schemas.ChatResponse)
def chat(data: schemas.ChatRequest, db: Session = Depends(get_db)):
    question = data.message.strip()
    lowered = question.lower()

    if any(word in lowered for word in ["게시", "커뮤니티", "검색", "팁"]):
        posts = (
            db.query(models.Post)
            .filter(
                or_(
                    models.Post.title.ilike(f"%{question}%"),
                    models.Post.content.ilike(f"%{question}%"),
                )
            )
            .order_by(models.Post.id.desc())
            .limit(3)
            .all()
        )
        if not posts:
            posts = db.query(models.Post).order_by(models.Post.id.desc()).limit(3).all()
        titles = "<br>".join(f"• {post.title}" for post in posts)
        return schemas.ChatResponse(answer=f"💬 최근 커뮤니티 게시글입니다.<br>{titles}")

    if any(word in lowered for word in ["관광", "경복궁", "타워", "한옥"]):
        return schemas.ChatResponse(
            answer="🏔️ 서울 대표 관광지로 경복궁, N서울타워, 북촌한옥마을을 추천합니다."
        )
    if any(word in lowered for word in ["축제", "행사", "이벤트"]):
        return schemas.ChatResponse(
            answer="🎉 서울의 대표 행사로 여의도 한강공원의 서울세계불꽃축제가 있습니다."
        )
    if any(word in lowered for word in ["숙소", "호텔", "숙박"]):
        return schemas.ChatResponse(
            answer="🏨 남산 인근 호텔이나 종로 한옥스테이를 여행 목적에 따라 선택해 보세요."
        )
    if any(word in lowered for word in ["음식", "맛집", "식사"]):
        return schemas.ChatResponse(
            answer="🍽️ 지역과 원하는 음식 종류를 함께 입력하면 더 구체적으로 안내할 수 있습니다."
        )

    return schemas.ChatResponse(
        answer="서울의 관광지, 축제, 숙박, 맛집 또는 커뮤니티 게시글에 대해 질문해 주세요."
    )
