from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class StudentBase(BaseModel):
    full_name: str
    student_card_number: Optional[str] = None
    group_name: str
    course: Optional[int] = None
    program_name: Optional[str] = None
    specialization: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DebtBase(BaseModel):
    discipline_name: str
    semester_origin: Optional[int] = None
    hours_remaining: Optional[int] = None
    credits_remaining: Optional[float] = None
    reassessment_deadline: Optional[date] = None

class DebtCreate(DebtBase):
    student_id: int
    discipline_id: Optional[int] = None

class Debt(DebtBase):
    id: int
    student_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True