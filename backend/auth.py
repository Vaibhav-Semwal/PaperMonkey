"""
Initializes the Firebase Admin SDK and exposes a FastAPI dependency that
verifies the Firebase ID token sent by the React frontend and returns the
decoded token (contains uid, email, etc).
"""
import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Header, HTTPException, status

_cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "serviceAccountKey.json")

if not firebase_admin._apps:
    if os.path.exists(_cred_path):
        cred = credentials.Certificate(_cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # Falls back to Application Default Credentials (e.g. on Cloud Run/GCP).
        firebase_admin.initialize_app()


async def get_current_firebase_user(authorization: str = Header(None)) -> dict:
    """
    Expects header:  Authorization: Bearer <Firebase ID token>
    Returns the decoded token dict, e.g. {"uid": "...", "email": "...", ...}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )
    id_token = authorization.split("Bearer ", 1)[1].strip()
    try:
        decoded_token = auth.verify_id_token(id_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase ID token",
        )
    return decoded_token
