from typing import Any
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class LearningModuleOut(BaseModel):
    id: int
    lang: str
    category: str
    title: str
    summary: str
    body: str
    quiz: list[QuizQuestion]


class QuizSubmitIn(BaseModel):
    module_id: int
    selected_option_index: int


class QuizResultOut(BaseModel):
    is_correct: bool
    correct_index: int
    explanation: str

