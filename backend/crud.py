from __future__ import annotations

from sqlalchemy.orm import Session

import models

# Fields that callers are allowed to update on IndividualPlanItem
_PLAN_ITEM_UPDATABLE = frozenset({"discipline_name", "control_form", "credits", "hours", "deadline"})


def get_student(db: Session, student_id: int) -> models.Student | None:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_student_by_card(db: Session, student_card_number: str) -> models.Student | None:
    return db.query(models.Student).filter(
        models.Student.student_card_number == student_card_number
    ).first()


def get_all_students(db: Session, skip: int = 0, limit: int = 100) -> list[models.Student]:
    return (
        db.query(models.Student)
        .order_by(models.Student.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_student(db: Session, student_id: int) -> bool:
    student = get_student(db, student_id)
    if student is None:
        return False
    db.delete(student)
    db.commit()
    return True


def get_dashboard_data(db: Session, student_id: int) -> dict | None:
    student = get_student(db, student_id)
    if student is None:
        return None

    debts          = db.query(models.Debt).filter(models.Debt.student_id == student_id).all()
    attested_items = db.query(models.AttestationItem).filter(models.AttestationItem.student_id == student_id).all()
    plan_items     = db.query(models.IndividualPlanItem).filter(models.IndividualPlanItem.student_id == student_id).all()

    total_credits     = sum(float(d.credits_remaining or 0) for d in debts)
    completed_credits = sum(float(a.credits or 0) for a in attested_items)

    return {
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "student_card_number": student.student_card_number,
            "group_name": student.group_name,
            "course": student.course,
            "program_name": student.program_name,
            "specialization": student.specialization,
            "status": student.status,
        },
        "progress": {
            "total_credits": total_credits,
            "completed_credits": completed_credits,
        },
        "all_debts": [
            {
                "id": d.id,
                "discipline_name": d.discipline_name,
                "hours_remaining": d.hours_remaining,
                "credits_remaining": d.credits_remaining,
                "deadline": d.reassessment_deadline,
                "status": d.status,
            }
            for d in debts
        ],
        "attested_items": [
            {
                "id": a.id,
                "discipline_name": a.discipline_name,
                "credits": a.credits,
                "control_form": a.control_form,
                "result": a.result,
                "attestation_type": a.attestation_type,
            }
            for a in attested_items
        ],
        "plan_items": [
            {
                "id": p.id,
                "discipline_name": p.discipline_name,
                "hours": p.hours,
                "credits": p.credits,
                "control_form": p.control_form,
                "deadline": p.deadline,
            }
            for p in plan_items
        ],
    }


def get_plan_item(db: Session, item_id: int) -> models.IndividualPlanItem | None:
    return db.query(models.IndividualPlanItem).filter(models.IndividualPlanItem.id == item_id).first()


def update_plan_item(db: Session, item_id: int, data: dict) -> models.IndividualPlanItem | None:
    item = get_plan_item(db, item_id)
    if item is None:
        return None
    for field, value in data.items():
        if field in _PLAN_ITEM_UPDATABLE:
            setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item
