from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint,DateTime,func
from sqlalchemy.orm import relationship
from database import Base

class ProfileModel(Base):
    __tablename__ = "profiles"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # Relationship to upvotes
    upvotes = relationship("UpvoteModel", back_populates="user")

class PostsModel(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    text_content = Column(String, nullable=False)
    media = Column(String, nullable=True)
    author = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Add upvote count for performance
    upvote_count = Column(Integer, default=0)
    
    # Relationship to upvotes
    upvotes = relationship("UpvoteModel", back_populates="post")

class UpvoteModel(Base):
    __tablename__ = "upvotes"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    
    # Ensure one upvote per user per post
    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='_user_post_upvote'),)
    
    # Relationships
    user = relationship("ProfileModel", back_populates="upvotes")
    post = relationship("PostsModel", back_populates="upvotes")





