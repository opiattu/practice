from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ─── Student ────────────────────────────────────────────────────────────────

class StudentResponse(BaseModel):
    id: int
    full_name: str
    student_card_number: Optional[str] = None
    group_name: Optional[str] = None
    course: Optional[int] = None
    program_name: Optional[str] = None
    specialization: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    full_name: str
    student_card_number: str
    group_name: Optional[str] = None
    course: Optional[int] = None
    program_name: Optional[str] = None
    specialization: Optional[str] = None


# ─── Plan items ─────────────────────────────────────────────────────────────

class PlanItemSummary(BaseModel):
    """Compact representation used inside DashboardResponse."""
    id: int
    discipline_name: str
    hours: Optional[int] = None
    credits: Optional[int] = None
    control_form: Optional[str] = None
    deadline: Optional[date] = None


class PlanItemResponse(PlanItemSummary):
    """Full representation returned by PATCH /plan-items/{id}."""
    student_id: int
    debt_id: Optional[int] = None

    model_config = {"from_attributes": True}


class PlanItemUpdate(BaseModel):
    discipline_name: Optional[str] = None
    control_form: Optional[str] = None
    credits: Optional[int] = None
    hours: Optional[int] = None
    deadline: Optional[date] = None


# ─── Dashboard sub-objects ───────────────────────────────────────────────────

class DebtResponse(BaseModel):
    id: int
    discipline_name: str
    hours_remaining: Optional[int] = None
    credits_remaining: Optional[int] = None
    deadline: Optional[date] = None
    status: str


class AttestationItemResponse(BaseModel):
    id: int
    discipline_name: str
    credits: Optional[int] = None
    control_form: Optional[str] = None
    result: Optional[str] = None
    attestation_type: Optional[str] = None


class ProgressResponse(BaseModel):
    total_credits: float
    completed_credits: float


class DashboardResponse(BaseModel):
    student: StudentResponse
    progress: ProgressResponse
    all_debts: list[DebtResponse]
    attested_items: list[AttestationItemResponse]
    plan_items: list[PlanItemSummary]


# ─── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    student_id: int
    disciplines_loaded: int
    debts_loaded: int
    plan_items_loaded: int
