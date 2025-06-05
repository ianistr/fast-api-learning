# routers/posts.py
from fastapi import APIRouter, HTTPException, Depends, status,Query
from sqlalchemy.orm import Session
from sqlalchemy import asc,desc
from uuid import uuid4
# Correctly import ProfileModel as your user model
from models import PostsModel, UpvoteModel, ProfileModel
from database import SessionLocal
from api_key import verify_api_key
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from .auth import get_current_user, SECRET_KEY, ALGORITHM # Keep this for routes that require authentication
from fastapi.security import OAuth2PasswordBearer # Import OAuth2PasswordBearer
from jose import JWTError, jwt # Import jwt and JWTError for token decoding
from datetime import datetime

router = APIRouter()

# Define oauth2_scheme here, assuming it's configured in auth.py with "/token"
# If your token URL is different, please adjust it accordingly.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# New scheme for optional authentication, set auto_error=False
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

# Pydantic models
class CreatePost(BaseModel):
    title: str
    text_content: str
    media: Optional[str]

class ReadPosts(BaseModel):
    id: str
    title: str
    text_content: str
    media: Optional[str]
    author: str
    created_at: datetime
    upvote_count: int

    class Config:
        orm_mode = True

class PostWithUpvoteStatus(BaseModel):
    id: str
    title: str
    text_content: str
    media: Optional[str]
    author: str
    created_at: datetime
    upvote_count: int
    user_has_upvoted: bool

class UpvoteResponse(BaseModel):
    action: str  # "added" or "removed"
    upvote_count: int
    user_has_upvoted: bool

class VoterInfo(BaseModel):
    id: str
    username: str

    class Config:
        orm_mode = True

# Upvote service functions
def toggle_upvote(db: Session, user_id: str, post_id: str):
    """Toggle upvote on a post"""
    # Check if user already upvoted
    existing_upvote = db.query(UpvoteModel).filter(
        UpvoteModel.user_id == user_id,
        UpvoteModel.post_id == post_id
    ).first()
    
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if existing_upvote:
        # Remove upvote
        db.delete(existing_upvote)
        post.upvote_count -= 1
        action = "removed"
        user_has_upvoted = False
    else:
        # Add upvote
        new_upvote = UpvoteModel(
            id=str(uuid4()),
            user_id=user_id,
            post_id=post_id
        )
        db.add(new_upvote)
        post.upvote_count += 1
        action = "added"
        user_has_upvoted = True
    
    db.commit()
    return {
        "action": action,
        "upvote_count": post.upvote_count,
        "user_has_upvoted": user_has_upvoted
    }

def has_user_upvoted(db: Session, user_id: str, post_id: str) -> bool:
    """Check if user has upvoted a specific post"""
    upvote = db.query(UpvoteModel).filter(
        UpvoteModel.user_id == user_id,
        UpvoteModel.post_id == post_id
    ).first()
    return upvote is not None

def get_posts_with_upvote_status(db: Session, user_id: str = None):
    """Get all posts with upvote status for a user"""
    posts = db.query(PostsModel).all()
    
    if not user_id:
        return [
            PostWithUpvoteStatus(
                id=post.id,
                title=post.title,
                text_content=post.text_content,
                media=post.media,
                author=post.author,
                created_at=post.created_at,
                upvote_count=post.upvote_count,
                user_has_upvoted=False
            )
            for post in posts
        ]
    
    # Get all user's upvotes in one query for efficiency
    post_ids = [post.id for post in posts]
    user_upvotes = db.query(UpvoteModel.post_id).filter(
        UpvoteModel.user_id == user_id,
        UpvoteModel.post_id.in_(post_ids)
    ).all()
    upvoted_post_ids = {upvote.post_id for upvote in user_upvotes}
    
    return [
        PostWithUpvoteStatus(
            id=post.id,
            title=post.title,
            text_content=post.text_content,
            media=post.media,
            author=post.author,
            created_at=post.created_at,
            upvote_count=post.upvote_count,
            user_has_upvoted=post.id in upvoted_post_ids
        )
        for post in posts
    ]

# New dependency for optional authentication
async def get_current_user_for_posts(
    token: Optional[str] = Depends(optional_oauth2_scheme), # Use the new optional scheme
    db: Session = Depends(get_db) # Add database dependency to fetch user
):
    """
    Attempts to get the current user. Returns the user object if authenticated,
    otherwise returns None without raising an HTTPException.
    This version directly decodes the token and fetches the ProfileModel object
    to ensure consistent user ID (UUID) usage.
    """
    if token is None:
        return None  # No token provided, so no current user
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None # Token exists but no username in payload
        
        # Fetch the actual ProfileModel object from the database using the username
        user = db.query(ProfileModel).filter(ProfileModel.username == username).first()
        
        return user # This will be None if user not found, or the actual ProfileModel object
    except JWTError:
        # Invalid token, return None for unauthenticated access
        return None
    except Exception:
        # Catch any other unexpected errors during token processing
        return None

# Routes
@router.post(
    "/create_post",
    response_model=ReadPosts,
    dependencies=[Depends(verify_api_key)]
)
def create_post(
    post: CreatePost,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        new_post = PostsModel(
            id=str(uuid4()),
            title=post.title,
            text_content=post.text_content,
            media=post.media or "",
            author=current_user.username,
            upvote_count=0  # Initialize upvote count
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

@router.get("/filtered_posts", response_model=List[ReadPosts], dependencies=[Depends(verify_api_key)])
def get_posts(
    db: Session = Depends(get_db),
    sort_by: Optional[str] = Query("id"),   # default to "id"
    order: Optional[str] = Query("desc"),   # "asc" or "desc"
    limit: int = Query(10, ge=1, le=100),   # limit between 1 and 100
    offset: int = Query(0, ge=0)            # pagination offset
):
    # Ensure the column exists in the model
    sort_column = getattr(PostsModel, sort_by, None)
    if not sort_column:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    # Apply sort direction
    if order == "asc":
        order_clause = asc(sort_column)
    else:
        order_clause = desc(sort_column)

    return (
        db.query(PostsModel)
        .order_by(order_clause)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/posts-with-upvotes", response_model=List[PostWithUpvoteStatus])
async def get_posts_with_upvotes(
    db: Session = Depends(get_db),
    current_user_optional: Optional[ProfileModel] = Depends(get_current_user_for_posts) # Type hint for clarity
):
    """Get all posts with upvote status for the current user (or no user if not logged in)"""
    # current_user_optional will now be a ProfileModel object or None
    return get_posts_with_upvote_status(db, current_user_optional.id if current_user_optional else None)

@router.post("/posts/{post_id}/upvote", response_model=UpvoteResponse)
def upvote_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Toggle upvote on a post"""
    try:
        result = toggle_upvote(db, current_user.id, post_id)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts/{post_id}/upvote-status")
def get_upvote_status(
    post_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Check if current user has upvoted a specific post"""
    # Verify post exists
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    has_upvoted = has_user_upvoted(db, current_user.id, post_id)
    return {
        "post_id": post_id,
        "user_has_upvoted": has_upvoted,
        "upvote_count": post.upvote_count
    }

  # route to get what users have voted on a post

@router.get("/posts/{post_id}/voters", response_model=List[VoterInfo], dependencies=[Depends(verify_api_key)])
def get_post_voters(
    post_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of users who have voted on a specific post.
    """
    # Verify post exists
    post = db.query(PostsModel).filter(PostsModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get all upvotes for the given post_id, and eager load the 'user' relationship
    upvotes = db.query(UpvoteModel).filter(UpvoteModel.post_id == post_id).all()
    
    # Extract voter information from the related ProfileModel objects
    voters = []
    for upvote in upvotes:
        if upvote.user: # Ensure the user relationship is loaded
            voters.append(VoterInfo(id=upvote.user.id, username=upvote.user.username))
            
    return voters
