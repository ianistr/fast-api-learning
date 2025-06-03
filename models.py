
from sqlalchemy import Column, String
from database import Base

class ProfileModel(Base):
    __tablename__ = "profiles"
    id = Column(String, primary_key=True, index=True)
    cnp = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)

class PostsModel(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    text_content = Column(String, nullable=False)
    media = Column(String, nullable=True)
    author = Column(String, nullable=False)
