from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from enum import Enum
from uuid import UUID, uuid4
import re

# Enums
class CourseCode(str, Enum):
    AI_101 = "AI-101"
    AI_201 = "AI-201"
    AI_202 = "AI-202"
    AI_301 = "AI-301"

class Weekday(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

class CourseSection(str, Enum):
    A = "A"
    B = "B"
    C = "C"

# Models
class Todo(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the todo")
    description: str = Field(..., min_length=1, description="Description of the todo item")
    due_date: Optional[datetime] = Field(None, description="Due date for the todo")

class Student(BaseModel):
    id: str = Field(..., min_length=3, max_length=50, description="Unique student ID")
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student")
    email: EmailStr = Field(..., description="Valid email address")
    phone: str = Field(..., pattern=r'^\+?[0-9]{10,15}$', description="Phone number with optional country code")
    course_code: CourseCode = Field(default=CourseCode.AI_101, description="Assigned course (default is AI-101)")

class ClassSchedule(BaseModel):
    day: Weekday = Field(..., description="Day of the week")
    time: str = Field(..., description="Time range (e.g., 10:00 AM - 12:00 PM)")

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        pattern = r"^\d{1,2}:\d{2} (AM|PM) - \d{1,2}:\d{2} (AM|PM)$"
        if not re.match(pattern, v):
            raise ValueError("Time must be in format 'HH:MM AM/PM - HH:MM AM/PM'")
        return v

class Enrollment(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique enrollment ID")
    course_code: CourseCode = Field(..., description="Course code for enrollment")
    section: CourseSection = Field(..., description="Course section")
    course_name: Optional[str] = Field(default=None, description="Auto-filled course name based on course code")
    instructor: str = Field(..., description="Name of the course instructor")
    schedule: List[ClassSchedule] = Field(..., description="List of class schedules")
    last_class_date: Optional[datetime] = Field(None, description="Date of the last class attended")
    last_class_covered: str = Field(..., description="Last class topic covered")
    todos: List[Todo] = Field(default_factory=list, description="Pending tasks for the student")
    covered_topics: List[str] = Field(default_factory=list, description="Topics covered so far in the course")
    next_class_time: Optional[datetime] = Field(None, description="Date and time of the next class")

    _course_titles = {
        CourseCode.AI_101: "Modern AI Python Programming",
        CourseCode.AI_201: "Fundamentals of Agentic AI and DACA AI-First Development",
        CourseCode.AI_202: "DACA Cloud-First Agentic AI Development",
        CourseCode.AI_301: "DACA Planet-Scale Distributed AI Agents",
    }

    @model_validator(mode="after")
    def set_course_name(self) -> "Enrollment":
        if not self.course_name:
            self.course_name = self._course_titles.get(self.course_code)
        return self

class CurrentTopic(BaseModel):
    course_code: CourseCode = Field(..., description="Course code")
    topic: str = Field(..., min_length=1, description="Current topic being covered")
    start_date: Optional[datetime] = Field(None, description="Date when the topic started")