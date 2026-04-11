from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


class RecommendedCourse(BaseModel):
    course_id: str
    title: str
    reason: str


class ChatResponse(BaseModel):
    answer: str
    recommended_courses: list[RecommendedCourse] = Field(default_factory=list)
