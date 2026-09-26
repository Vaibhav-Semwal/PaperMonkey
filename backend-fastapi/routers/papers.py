from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from auth import get_current_firebase_user
from users.models import Profile, Paper
from llm.graph import run_generation_pipeline

from db import profiles as profiles_db, papers as papers_db
from schemas.papers import PaperCreate, QuestionEdit

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("")
async def create_paper(payload: PaperCreate, user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet. Call /api/register first.")
    if profile.role != Profile.Role.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can create papers")
    paper = await papers_db.create_draft_paper(profile, payload)
    return {
        "id": paper.id, "paper_name": paper.paper_name, "topics": paper.topics,
        "external_links": paper.external_links, "sections": paper.sections,
        "status": paper.status, "created_at": paper.created_at.isoformat(),
    }


@router.get("")
async def list_papers(user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=403, detail="Teachers only")
    papers = await papers_db.list_papers(profile)
    return [{**p, "created_at": p["created_at"].isoformat()} for p in papers]


@router.get("/{paper_id}")
async def get_paper(paper_id: int, user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet.")
    paper = await papers_db.get_paper_owned(paper_id, profile)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return await papers_db.paper_detail_with_questions(paper)


@router.post("/{paper_id}/generate-questions")
async def generate_questions(paper_id: int, background_tasks: BackgroundTasks, user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None or profile.role != Profile.Role.TEACHER:
        raise HTTPException(status_code=403, detail="Teachers only")
    paper = await papers_db.get_paper_owned(paper_id, profile)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper.status == Paper.Status.GENERATING:
        raise HTTPException(status_code=409, detail="Generation already in progress")

    await papers_db.mark_generating(paper_id)
    background_tasks.add_task(run_generation_pipeline, paper_id)
    return {"status": "generating"}


@router.patch("/{paper_id}/questions/{question_id}")
async def edit_question(paper_id: int, question_id: int, payload: QuestionEdit, user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet.")
    q = await papers_db.update_question(question_id, profile, payload)
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"id": q.id, "question_text": q.question_text, "answer_text": q.answer_text}


@router.post("/{paper_id}/publish")
async def publish_paper(paper_id: int, user=Depends(get_current_firebase_user)):
    profile = await profiles_db.get_profile(user["uid"])
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet.")
    paper = await papers_db.get_paper_owned(paper_id, profile)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    updated = await papers_db.publish_if_ready(paper)
    if updated is None:
        raise HTTPException(status_code=400, detail="Paper must be status=ready before publishing")
    return {"status": updated.status}