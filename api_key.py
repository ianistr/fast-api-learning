from fastapi import  Header, HTTPException
from typing import Optional



# === API Key Config ===
API_KEY = "ianisaremere"

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key