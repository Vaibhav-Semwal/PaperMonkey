from django.db import models


class Profile(models.Model):
    """
    One row per Firebase-authenticated user.

    Firebase owns identity/passwords. This table just maps a Firebase UID
    to an app-level role so we know which dashboard to show and what data
    that user is allowed to see.
    """

    class Role(models.TextChoices):
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"

    firebase_uid = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField()
    display_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} ({self.role})"


class Paper(models.Model):
    """
    A question paper being drafted by a teacher.

    `topics` is a JSON list of strings.
    `external_links` is a JSON list of URL strings.
    `sections` is a JSON list of objects, e.g.:
        [{"section": "A", "num_questions": 10, "marks_per_question": 2}, ...]
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"
        PUBLISHED = "published", "Published"

    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="papers")
    paper_name = models.CharField(max_length=255)
    topics = models.JSONField(default=list, blank=True)
    external_links = models.JSONField(default=list, blank=True)
    sections = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.paper_name} ({self.status})"


class QuestionBank(models.Model):
    """
    One row per generated question. Independent of any single paper so it
    can be reused or searched later, even across different papers.
    """

    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="question_bank")
    question_text = models.TextField()
    answer_text = models.TextField()
    topic = models.CharField(max_length=255, blank=True)
    marks = models.PositiveIntegerField()
    source_link = models.URLField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:60]


class PaperQuestion(models.Model):
    """
    Assigns a QuestionBank entry into a specific paper's section slot.
    """

    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="paper_questions")
    section = models.CharField(max_length=1)
    order = models.PositiveIntegerField(default=0)
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name="paper_links")

    class Meta:
        ordering = ["section", "order"]
        unique_together = ("paper", "section", "order")

    def __str__(self):
        return f"{self.paper.paper_name} - Section {self.section} #{self.order}"