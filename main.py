from fastapi import FastAPI, Header, HTTPException, Depends,Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional, List
import uuid
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from util_apis import check_palindrome,check_even


from api_key import verify_api_key




# === Database Setup ===
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./local.db')

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# === Database Models ===
class ProfileModel(Base):
    __tablename__ = "profiles"
    id = Column(String, primary_key=True, index=True)  # UUID
    cnp = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)


class PostsModel(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True, index=True)
    text_content=Column(String,nullable=False)
    media=Column(String,nullable=True)
    author=Column(String,nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)

# === Pydantic Models ===
class ProfileCreate(BaseModel):
    cnp: str
    first_name: str
    last_name:str
    email: str
    password: str

class ProfileOut(BaseModel):
    id: str
    cnp: str
    first_name: str
    last_name:str
    email: str

    class Config:
        orm_mode = True

class CreatePost(BaseModel):
    text_content:str
    media:str
    author:str

class ReadPosts(BaseModel):
    id:str
    text_content:str
    media:str
    author:str


class NumberInput(BaseModel):
    number:int

class StringInput(BaseModel):
    word:str

# === FastAPI app ===
app = FastAPI( redoc_url=None) #docs_url=None, for no docs


app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the router with a prefix if you want
app.include_router(check_palindrome.router, prefix="/api")
app.include_router(check_even.router, prefix="/api")

# Set up Jinja templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request,name:str="guest"):
    return templates.TemplateResponse("index.html", {"request": request, "title": f"Hello {name}"})



@app.get("/check_palindrome", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("check_palindrome.html", {"request": request, "title":f"Check if a word is a palindrome!"})



@app.get("/check_even", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("check_even.html", {"request": request, "title":f"Check if a number is even!"})

@app.post("/create_post",response_model=ReadPosts,dependencies=[Depends(verify_api_key)])
def create_post(post:CreatePost):
    db= SessionLocal()
    try:
        new_post=PostsModel(
            id=str(uuid.uuid4()),
            text_content=post.text_content,
            media=post.media,
            author=post.author
            
            )
        

        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/posts", response_model=List[ReadPosts], dependencies=[Depends(verify_api_key)])
def get_profiles():
    db = SessionLocal()
    try:
        posts = db.query(PostsModel).all()
        return posts
    finally:
        db.close()



@app.post("/create_profiles", response_model=ProfileOut, dependencies=[Depends(verify_api_key)])
def create_profile(profile: ProfileCreate):
    db = SessionLocal()
    try:
        # Check if number is already registered
        existing = db.query(ProfileModel).filter(ProfileModel.cnp == profile.cnp).first()
        if existing:
            raise HTTPException(status_code=400, detail="Number already registered")

        # Create new profile
        new_profile = ProfileModel(
            id=str(uuid.uuid4()),
            cnp=profile.cnp,
            first_name=profile.first_name,
            last_name=profile.last_name,
            email=profile.email,
            password=profile.password  # In real app, hash this!
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return new_profile

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/profiles", response_model=List[ProfileOut], dependencies=[Depends(verify_api_key)])
def get_profiles():
    db = SessionLocal()
    try:
        profiles = db.query(ProfileModel).all()
        return profiles
    finally:
        db.close()






    




