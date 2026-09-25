from typing import Literal
from pydantic import BaseModel, Field

Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility"]
Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    user_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=500)
    goal: Goal
    intensity: Intensity


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    feedback: str = Field(min_length=3, max_length=2000)


class Exercise(BaseModel):
    name: str
    sets: str
    reps_or_duration: str
    rest: str


class WorkoutDay(BaseModel):
    day: str
    focus: str
    warmup: str
    exercises: list[Exercise]
    cooldown: str


class WorkoutPlan(BaseModel):
    summary: str
    days: list[WorkoutDay] = Field(min_length=7, max_length=7)
    safety_notes: list[str]


class NutritionTip(BaseModel):
    tip: str
    recovery_note: str
