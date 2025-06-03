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
from util_apis import posts,auth


from database import Base,engine
import models

from api_key import verify_api_key



# Create tables
Base.metadata.create_all(bind=engine)






# === FastAPI app ===
app = FastAPI( redoc_url=None) #docs_url=None, for no docs


app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the router with a prefix if you want

app.include_router(posts.router, prefix="/api")
app.include_router(auth.router, prefix="/auth")

# Set up Jinja templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request,name:str="guest"):
    return templates.TemplateResponse("index.html", {"request": request, "title": f"{name}"})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request, "title": "Profile"})











    




