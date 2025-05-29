from fastapi import APIRouter, Depends
from api_key import verify_api_key
from pydantic import BaseModel

router = APIRouter()

class StringInput(BaseModel):
    word: str

@router.post("/check_palindrome", response_model=bool, dependencies=[Depends(verify_api_key)])
async def check_palindrome(word: StringInput) -> bool:
    return word.word == word.word[::-1]