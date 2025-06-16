import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
from mcp.server.fastmcp import FastMCP, Context

from Data.dummy_data import student_store, enrollment_store, topic_store
from Models.pydantic_models import Enrollment, Student, CourseCode, CourseSection, ClassSchedule

# Constants
ERROR_CODES = {
    "STUDENT_NOT_FOUND": "Student not found",
    "ENROLLMENT_NOT_FOUND": "No enrollment found for course",
    "SCHEDULE_NOT_FOUND": "No schedule found for course",
    "NO_NEXT_CLASS": "No upcoming classes scheduled",
    "TOPIC_NOT_FOUND": "No current topic found for course",
    "INTERNAL_ERROR": "Internal server error"
}

# Configure logging with proper format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Response type definitions
class ErrorResponse(TypedDict):
    code: str
    message: str

class ApiResponse(TypedDict):
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[ErrorResponse]

def create_error_response(code: str, message: str) -> ApiResponse:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message
        },
        "data": None
    }

def create_success_response(data: Dict[str, Any]) -> ApiResponse:
    """Create a standardized success response."""
    return {
        "success": True,
        "data": data,
        "error": None
    }

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
def get_student_info(student_id: str) -> ApiResponse:
    """
    Get student profile and enrollment details.
    
    Args:
        student_id: Unique identifier for the student
        
    Returns:
        Dict containing student and enrollment information or error details
    """
    try:
        student = find_student(student_id)
        if not student:
            return create_error_response("STUDENT_NOT_FOUND", ERROR_CODES["STUDENT_NOT_FOUND"])
        
        enrollment = find_enrollment(student.course_code)
        if not enrollment:
            return create_error_response(
                "ENROLLMENT_NOT_FOUND", 
                f"{ERROR_CODES['ENROLLMENT_NOT_FOUND']} {student.course_code}"
            )
        
        return create_success_response({
            "student": student.model_dump(),
            "enrollment": enrollment.model_dump()
        })
    except Exception as e:
        logger.error(f"Error in get_student_info: {str(e)}")
        return create_error_response("INTERNAL_ERROR", ERROR_CODES["INTERNAL_ERROR"])


# --- Tools ---

## --- Class Schedule ---
@mcp.tool(
    name="get_class_schedule",
    description="Retrieve the class schedule for a specific course and section"
)
def get_class_schedule(course_code: CourseCode, section: CourseSection) -> ApiResponse:
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
            return create_error_response(
                "SCHEDULE_NOT_FOUND",
                f"{ERROR_CODES['SCHEDULE_NOT_FOUND']} {course_code} section {section}"
            )
        
        return create_success_response({
            "course_code": course_code,
            "section": section,
            "schedule": [session.model_dump() for session in schedule_info.schedule]
        })
            
    except Exception as e:
        logger.error(f"Error in get_class_schedule: {str(e)}")
        return create_error_response("INTERNAL_ERROR", ERROR_CODES["INTERNAL_ERROR"])


## --- Next Class Time ---
@mcp.tool(
    name="get_next_class",
    description="Retrieve the next scheduled class time for a specific course and section",
)
def get_next_class_time(course_code: CourseCode, section: CourseSection) -> ApiResponse:
    """Retrieve the next class time for a given course and section."""
    try:
        # Find matching enrollment
        enrollment = next(
            (e for e in enrollment_store 
             if e.course_code == course_code and e.section == section),
            None
        )
        
        if not enrollment:
            return create_error_response(
                "SCHEDULE_NOT_FOUND",
                f"{ERROR_CODES['SCHEDULE_NOT_FOUND']} {course_code} section {section}"
            )
            
        if not enrollment.next_class_time:
            return create_error_response("NO_NEXT_CLASS", ERROR_CODES["NO_NEXT_CLASS"])
            
        return create_success_response({
            "course_code": course_code,
            "section": section,
            "next_class_time": enrollment.next_class_time.isoformat(),
            "instructor": enrollment.instructor
        })
            
    except Exception as e:
        logger.error(f"Error in get_next_class_time: {str(e)}")
        return create_error_response("INTERNAL_ERROR", ERROR_CODES["INTERNAL_ERROR"])


## --- Course Current Topic ---
@mcp.tool(
    name="get_course_topic",
    description="Retrieve the current topic being covered in a specific course",
)
def get_course_current_topic(course_code: CourseCode) -> ApiResponse:
    """Retrieve the current topic for a given course."""
    try:
        # Find matching topic
        topic = next(
            (t for t in topic_store if t.course_code == course_code),
            None
        )
        
        if not topic:
            return create_error_response(
                "TOPIC_NOT_FOUND",
                f"{ERROR_CODES['TOPIC_NOT_FOUND']} {course_code}"
            )
            
        return create_success_response(topic.model_dump())
            
    except Exception as e:
        logger.error(f"Error in get_course_current_topic: {str(e)}")
        return create_error_response("INTERNAL_ERROR", ERROR_CODES["INTERNAL_ERROR"])


## --- Student's Course Covered Topics ---
@mcp.tool(
    name="get_covered_topics",
    description="Retrieve the list of topics covered so far in the student's enrolled course",
)
def get_course_covered_topics(student_id: str) -> ApiResponse:
    """Retrieve the covered topics for a student's enrolled course."""
    try:
        # Find student
        student = find_student(student_id)
        if not student:
            return create_error_response("STUDENT_NOT_FOUND", ERROR_CODES["STUDENT_NOT_FOUND"])
            
        # Find enrollment using student's course code
        enrollment = next(
            (e for e in enrollment_store 
             if e.course_code == student.course_code),
            None
        )
        
        if not enrollment:
            return create_error_response(
                "ENROLLMENT_NOT_FOUND",
                f"{ERROR_CODES['ENROLLMENT_NOT_FOUND']} {student.course_code}"
            )
            
        return create_success_response({
            "student_id": student_id,
            "course_code": student.course_code,
            "course_name": enrollment.course_name,
            "instructor": enrollment.instructor,
            "covered_topics": enrollment.covered_topics
        })
            
    except Exception as e:
        logger.error(f"Error in get_course_covered_topics: {str(e)}")
        return create_error_response("INTERNAL_ERROR", ERROR_CODES["INTERNAL_ERROR"])


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