from fastapi import APIRouter, Depends
from api_key import verify_api_key
from pydantic import BaseModel


router = APIRouter()

class NumberInput(BaseModel):
    number: int




@router.post("/check_even", response_model=bool, dependencies=[Depends(verify_api_key)])
async def check_even(number:NumberInput)->bool:
    return number.number%2==0