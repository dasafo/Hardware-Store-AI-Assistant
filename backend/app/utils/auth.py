# utils/auth.py
from fastapi import Header, HTTPException, status

API_KEY = "super-secret-admin"

def admin_guard(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return True
