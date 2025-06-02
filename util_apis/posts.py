# routers/posts.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from models import PostsModel
from database import SessionLocal
from api_key import verify_api_key
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# Pydantic models
class CreatePost(BaseModel):
    title: str
    text_content: str
    media: Optional[str]
    author: str

class ReadPosts(BaseModel):
    id: str
    title: str
    text_content: str
    media: Optional[str]
    author: str

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create_post", response_model=ReadPosts, dependencies=[Depends(verify_api_key)])
def create_post(post: CreatePost, db: Session = Depends(get_db)):
    try:
        new_post = PostsModel(
            id=str(uuid4()),
            title=post.title,
            text_content=post.text_content,
            media=post.media or "",
            author=post.author
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts", response_model=List[ReadPosts], dependencies=[Depends(verify_api_key)])
def get_posts(db: Session = Depends(get_db)):
    return db.query(PostsModel).all()
