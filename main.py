from fastapi import FastAPI, Header, HTTPException, Depends,Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional, List
import uuid

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from util_apis import check_palindrome,check_even,posts


from database import Base,engine
import models

from api_key import verify_api_key







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
app.include_router(posts.router, prefix="/api")

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








    




