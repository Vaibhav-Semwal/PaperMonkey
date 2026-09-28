from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_firebase_user
from database.models import Profile

from database import profiles as profiles_db
from schemas.account import RegisterPayload

router = APIRouter(tags=["account"])


@router.get("/api/health")
def health():
    return {"status": "ok"}


@router.post("/api/register")
async def register(payload: RegisterPayload, user=Depends(get_current_firebase_user)):
    if payload.role not in (Profile.Role.TEACHER, Profile.Role.STUDENT):
        raise HTTPException(status_code=400, detail="role must be 'teacher' or 'student'")
    profile, created = await profiles_db.get_or_create_profile(
        uid=user["uid"], email=user.get("email", ""),
        display_name=payload.display_name, role=payload.role,
    )
    return {
        "created": created, "uid": profile.firebase_uid, "email": profile.email,
        "display_name": profile.display_name, "role": profile.role,
    }


@router.get("/api/me")
async def me(user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet. Call /api/register first.")
    return {
        "uid": profile.firebase_uid, "email": profile.email,
        "display_name": profile.display_name, "role": profile.role,
    }


@router.get("/api/dashboard")
async def dashboard(user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet. Call /api/register first.")
    if profile.role == Profile.Role.TEACHER:
        return {
            "role": "teacher",
            "message": f"Hello World, Teacher {profile.display_name or profile.email}!",
            "widgets": ["My Classes", "Grade Submissions", "Student Roster"],
        }
    return {
        "role": "student",
        "message": f"Hello World, Student {profile.display_name or profile.email}!",
        "widgets": ["My Courses", "My Grades", "Assignments Due"],
    }