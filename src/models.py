import uuid as id
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class QuestionBank(models.Model):
    uuid = models.UUIDField(default= id.uuid4, primary_key=True, editable=False, unique=True)
    question = models.TextField(blank="empty question")
    answer = models.TextField(blank="empty answer")
    published_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.published_date}]{self.question}"

class Papers(models.Model):
    uuid = models.UUIDField(default= id.uuid4, primary_key=True, editable=False, unique=True)
    creator_name = models.CharField(max_length=50, default="anonymous")
    paper_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.paper_name}"

class PaperQuestion(models.Model): 
    class Difficulty(models.IntegerChoices):
        UNKNOWN = 0, ('unknown')
        EASY = 1, ('easy')
        MEDIUM = 2, ('medium')
        HARD = 3, ('hard')

        @classmethod
        def from_label(cls, label):
            for value, lbl in cls.choices:
                if lbl.lower() == label.lower():
                    return value
            return cls.UNKNOWN

    question = models.OneToOneField(QuestionBank, on_delete= models.CASCADE)
    marks = models.IntegerField()
    section = models.IntegerField()
    difficulty = models.IntegerField(
        choices = Difficulty.choices,
        default = Difficulty.UNKNOWN
    )
    paper = models.ForeignKey(
        Papers, 
        on_delete = models.CASCADE, 
        related_name = 'questions'
    )

    def __str__(self):
        return f"{self.section}| {self.difficulty} | {self.marks} |{self.question}"

class Users(AbstractUser):
    class AccountType(models.IntegerChoices):
        STUDENT = 1, ('Student')
        TEACHER = 2, ('Teacher')

    account_type = models.IntegerField(
        choices = AccountType.choices,
        default = AccountType.STUDENT
    )
    preferences = models.JSONField(default=dict, blank=True, auto_created=True)
    saved_papers = models.ManyToManyField(Papers, blank=True)

    def __str__(self):
        return f""" [{self.AccountType(self.account_type).label}]|{self.username}|
                     saved papers {self.saved_papers.count()}                                 """
    
class CrawledPage(models.Model):
    url = models.URLField(unique=True, max_length=2048)
    title = models.CharField(max_length=512, blank=True)
    html_content = models.TextField(blank=True)
    status_code = models.IntegerField(default=200)
    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    etag = models.CharField(max_length=256, blank=True)
    content_type = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ["-fetched_at"]


class CrawledLink(models.Model):
    source_page = models.ForeignKey(
        CrawledPage, on_delete=models.CASCADE, related_name="links"
    )
    target_url = models.URLField(max_length=2048)

    class Meta:
        unique_together = ("source_page", "target_url")