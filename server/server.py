import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP, Context

from Data.dummy_data import student_store, enrollment_store, topic_store
from Models.pydantic_models import Enrollment, Student, CourseCode, CourseSection, ClassSchedule


# Configure logging with proper format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize MCP server with proper configuration
mcp = FastMCP(
    name="StudentContextMCP",
    description="MCP server for managing student context, enrollments, and course progress",
    # Important for MCPServerStreamableHttp client in openai-agents-python
    # The client will handle sessions if needed, server can be stateless.
    stateless_http=True,
    json_response=True, # Generally easier for HTTP clients if they don't need full SSE parsing
)


# Helper functions for data access
def find_student(student_id: str) -> Optional[Student]:
    """Find a student by their ID."""
    try:
        return next((student for student in student_store if student.id == student_id), None)
    except Exception as e:
        logger.error(f"Error finding student {student_id}: {str(e)}")
        return None


def find_enrollment(course_code: CourseCode) -> Optional[Enrollment]:
    """Find an enrollment by course code."""
    try:
        return next((enrollment for enrollment in enrollment_store if enrollment.course_code == course_code), None)
    except Exception as e:
        logger.error(f"Error finding enrollment for course {course_code}: {str(e)}")
        return None


# --- Resources ---

## --- Student Profile ---
@mcp.resource(
    uri="students://{student_id}/profile",
    name="Get Student Profile",
    description="Get detailed student profile including enrollment information",
    mime_type="application/json"
)
def get_student_info(student_id: str) -> Dict[str, Any]:
    """
    Get student profile and enrollment details.
    
    Args:
        student_id: Unique identifier for the student
        
    Returns:
        Dict containing student and enrollment information or error details
    """
    student = find_student(student_id)
    if not student:
        return {
            "success": False,
            "error": {
                "code": "STUDENT_NOT_FOUND",
                "message": "Student not found",
            }
        }
    
    enrollment = find_enrollment(student.course_code)
    if not enrollment:
        return {
            "success": False,
            "error": {
                "code": "ENROLLMENT_NOT_FOUND",
                "message": f"No enrollment found for course {student.course_code}"
            }
        }
    
    return {
        "success": True,
        "data": {
            "student": student.model_dump(),
            "enrollment": enrollment.model_dump()
        }
    }


# --- Tools ---

## --- Class Schedule ---
@mcp.tool(
    name="get_class_schedule",
    description="Retrieve the class schedule for a specific course and section"
)
def get_class_schedule(course_code: CourseCode, section: CourseSection) -> Dict[str, Any]:
    """
    Retrieve the class schedule for a given course and section.
    
    Args:
        context: MCP context
        course_code: Course identifier
        section: Section identifier
        
    Returns:
        Dict containing schedule information or error details
    """
    try:
        # Find matching enrollment
        schedule_info = next(
            (enrollment for enrollment in enrollment_store 
             if enrollment.course_code == course_code and enrollment.section == section),
            None
        )
        
        if not schedule_info:
            return {
                "success": False,
                "error": {
                    "code": "SCHEDULE_NOT_FOUND",
                    "message": f"No schedule found for {course_code} section {section}"
                }
            }
        
        return {
            "success": True,
            "data": {
                "course_code": course_code,
                "section": section,
                "schedule": [session.model_dump() for session in schedule_info.schedule]
            }
        }
            
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch schedule"
            }
        }


## --- Next Class Time ---
@mcp.tool(
    name="get_next_class",
    description="Retrieve the next scheduled class time for a specific course and section",
)
def get_next_class_time(course_code: CourseCode, section: CourseSection) -> Dict[str, Any]:
    """Retrieve the next class time for a given course and section."""
    try:
        # Find matching enrollment
        enrollment = next(
            (e for e in enrollment_store 
             if e.course_code == course_code and e.section == section),
            None
        )
        
        if not enrollment:
            return {
                "success": False,
                "error": {
                    "code": "SCHEDULE_NOT_FOUND",
                    "message": f"No schedule found for {course_code} section {section}"
                }
            }
            
        if not enrollment.next_class_time:
            return {
                "success": False,
                "error": {
                    "code": "NO_NEXT_CLASS",
                    "message": "No upcoming classes scheduled"
                }
            }
            
        return {
            "success": True,
            "data": {
                "course_code": course_code,
                "section": section,
                "next_class_time": enrollment.next_class_time.isoformat(),
                "instructor": enrollment.instructor
            }
        }
            
    except Exception as e:
        logger.error(f"Error fetching next class time: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch next class time"
            }
        }


## --- Course Current Topic ---
@mcp.tool(
    name="get_course_topic",
    description="Retrieve the current topic being covered in a specific course",
)
def get_course_current_topic(course_code: CourseCode) -> Dict[str, Any]:
    """Retrieve the current topic for a given course."""
    try:
        # Find matching topic
        topic = next(
            (t for t in topic_store if t.course_code == course_code),
            None
        )
        
        if not topic:
            return {
                "success": False,
                "error": {
                    "code": "TOPIC_NOT_FOUND",
                    "message": f"No current topic found for course {course_code}"
                }
            }
            
        return {
            "success": True,
            "data": topic.model_dump()
        }
            
    except Exception as e:
        logger.error(f"Error fetching current topic: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch current topic"
            }
        }


## --- Student's Course Covered Topics ---
@mcp.tool(
    name="get_covered_topics",
    description="Retrieve the list of topics covered so far in the student's enrolled course",
)
def get_course_covered_topics(student_id: str) -> Dict[str, Any]:
    """Retrieve the covered topics for a student's enrolled course."""
    try:
        # Find student
        student = find_student(student_id)
        if not student:
            return {
                "success": False,
                "error": {
                    "code": "STUDENT_NOT_FOUND",
                    "message": "Student not found"
                }
            }
            
        # Find enrollment using student's course code
        enrollment = next(
            (e for e in enrollment_store 
             if e.course_code == student.course_code),
            None
        )
        
        if not enrollment:
            return {
                "success": False,
                "error": {
                    "code": "ENROLLMENT_NOT_FOUND",
                    "message": f"No enrollment found for course {student.course_code}"
                }
            }
            
        return {
            "success": True,
            "data": {
                "student_id": student_id,
                "course_code": student.course_code,
                "course_name": enrollment.course_name,
                "instructor": enrollment.instructor,
                "covered_topics": enrollment.covered_topics
            }
        }
            
    except Exception as e:
        logger.error(f"Error fetching covered topics: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch covered topics"
            }
        }


# # --- Main entry point to run the server ---

streamable_http_app = mcp.streamable_http_app()
logger.info(f"Starting {streamable_http_app}")


if __name__ == "__main__":
    try:
        port = 8000
        logger.info(f"Starting server on port {port}")
        import uvicorn
        uvicorn.run("server:streamable_http_app", host="0.0.0.0", port=port, reload=True, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise