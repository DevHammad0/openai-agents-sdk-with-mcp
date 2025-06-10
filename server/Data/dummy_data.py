from Models.pydantic_models import Student, Enrollment, ClassSchedule, CourseCode, Weekday, CourseSection, CurrentTopic, Todo
from datetime import datetime
from uuid import uuid4




# In-memory data store
student_store = [
    Student(
        id="S123",
        name="Ayaan Qureshi",
        email="ayaan.qureshi@example.com",
        phone="+923001112233",
        course_code=CourseCode.AI_101
    )
]

enrollment_store = [
    Enrollment(
        id=uuid4(),
        course_code=CourseCode.AI_101,
        section=CourseSection.A,
        instructor="Sajid Khan",
        schedule=[
            ClassSchedule(day=Weekday.MONDAY, time="10:00 AM - 11:30 AM"),
            ClassSchedule(day=Weekday.WEDNESDAY, time="10:00 AM - 11:30 AM")
        ],
        last_class_date=datetime(2025, 6, 2, 10, 0),
        last_class_covered="Introduction to Python",
        todos=[
            Todo(description="Complete assignment 1", due_date=datetime(2025, 6, 10)),
            Todo(description="Read chapter 3", due_date=datetime(2025, 6, 10))
        ],
        covered_topics=["Python Basics", "Introduction to Variables"],
        next_class_time=datetime(2025, 6, 9, 10, 0)
    )
]

topic_store = [
    CurrentTopic(
        course_code=CourseCode.AI_101,
        topic="Introduction to Lists",
        start_date=datetime(2025, 6, 2)
    )
]




# # --------------------
# # Dummy Data (in-memory)
# # --------------------

# dummy_student = Student(
#     id="stu-001",
#     name="Ayaan Qureshi",
#     email="ayaan.qureshi@example.com",
#     phone="+923001112233",
#     course_code=CourseCode.AI_101
# )


# dummy_schedule = [
#     ClassSchedule(day=Weekday.MONDAY, time="10:00 AM - 12:00 PM"),
#     ClassSchedule(day=Weekday.WEDNESDAY, time="10:00 AM - 12:00 PM"),
#     ClassSchedule(day=Weekday.FRIDAY, time="10:00 AM - 12:00 PM")
# ]

# dummy_enrollment = Enrollment(
#     id="enr-101",
#     course_code=CourseCode.AI_101,
#     instructor="Sajid Khan",
#     schedule=dummy_schedule,
#     last_class_covered="Introduction to Python Functions",
#     todos=[
#         "Submit assignment on variables and data types",
#         "Review for functions quiz"
#     ],
#     covered_topics=[
#         "Python Setup & Syntax",
#         "Data Types",
#         "Control Flow",
#         "Loops",
#         "Functions"
#     ]
# )
