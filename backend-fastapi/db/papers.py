import django_setup  # noqa: F401  (must run before importing Django models)

from asgiref.sync import sync_to_async

from users.models import Profile, Paper, QuestionBank


@sync_to_async
def create_draft_paper(profile, payload):
    return Paper.objects.create(
        teacher=profile,
        paper_name=payload.paper_name,
        topics=payload.topics,
        external_links=payload.external_links,
        sections=[s.model_dump() for s in payload.sections],
        status=Paper.Status.DRAFT,
    )

@sync_to_async
def list_papers(profile):
    if profile.role == Profile.Role.STUDENT:
        return list(
            Paper.objects.all()
            .select_related("teacher")
            .order_by("-created_at")
            .values("id", "paper_name", "teacher__display_name", "status", "created_at")[:100]
        )
    else: 
        return list(
            Paper.objects.filter(teacher=profile)
            .order_by("-created_at")
            .values("id", "paper_name", "status", "created_at")
        )


@sync_to_async
def get_paper_owned(paper_id: int, profile):
    try:
        return Paper.objects.get(id=paper_id, teacher=profile)
    except Paper.DoesNotExist:
        return None


@sync_to_async
def paper_detail_with_questions(paper):
    grouped = {}
    for pq in paper.paper_questions.select_related("question").all():
        grouped.setdefault(pq.section, []).append({
            "paper_question_id": pq.id,
            "question_id": pq.question.id,
            "question_text": pq.question.question_text,
            "answer_text": pq.question.answer_text,
            "marks": pq.question.marks,
        })
    return {
        "id": paper.id,
        "paper_name": paper.paper_name,
        "topics": paper.topics,
        "external_links": paper.external_links,
        "sections": paper.sections,
        "status": paper.status,
        "error_message": paper.error_message,
        "questions_by_section": grouped,
    }


@sync_to_async
def mark_generating(paper_id: int):
    Paper.objects.filter(id=paper_id).update(status=Paper.Status.GENERATING, error_message="")


@sync_to_async
def update_question(question_id: int, profile, payload):
    try:
        q = QuestionBank.objects.get(id=question_id, teacher=profile)
    except QuestionBank.DoesNotExist:
        return None
    q.question_text = payload.question_text
    q.answer_text = payload.answer_text
    q.save(update_fields=["question_text", "answer_text"])
    return q


@sync_to_async
def publish_if_ready(paper):
    if paper.status != Paper.Status.READY:
        return None
    paper.status = Paper.Status.PUBLISHED
    paper.save(update_fields=["status"])
    return paper