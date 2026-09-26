from typing import List
from pydantic import BaseModel, Field, field_validator

from constants.values import VALID_SECTIONS


class SectionInput(BaseModel):
    section: str
    num_questions: int = Field(ge=1, le=25)
    marks_per_question: int = Field(ge=1)

    @field_validator("section")
    @classmethod
    def section_must_be_valid(cls, v):
        v = v.strip().upper()
        if v not in VALID_SECTIONS:
            raise ValueError(f"section must be one of {VALID_SECTIONS}")
        return v


class PaperCreate(BaseModel):
    paper_name: str = Field(min_length=1, max_length=255)
    topics: List[str] = Field(default_factory=list)
    external_links: List[str] = Field(default_factory=list)
    sections: List[SectionInput] = Field(min_length=1, max_length=5)

    @field_validator("sections")
    @classmethod
    def sections_must_be_unique(cls, v):
        letters = [s.section for s in v]
        if len(letters) != len(set(letters)):
            raise ValueError("Each section (A-E) can only be used once")
        return v


class QuestionEdit(BaseModel):
    question_text: str
    answer_text: str