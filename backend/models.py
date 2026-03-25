from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    student_card_number = Column(String, unique=True, nullable=False, index=True)
    group_name = Column(String, nullable=True)
    course = Column(Integer, nullable=True)
    program_name = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    status = Column(String, default="active")

    debts = relationship("Debt", back_populates="student", cascade="all, delete-orphan")
    attestation_items = relationship("AttestationItem", back_populates="student", cascade="all, delete-orphan")
    individual_plan_items = relationship("IndividualPlanItem", back_populates="student", cascade="all, delete-orphan")


class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    discipline_name = Column(String, nullable=False)
    hours_remaining = Column(Integer, nullable=True)
    credits_remaining = Column(Integer, nullable=True)
    reassessment_deadline = Column(Date, nullable=True)
    status = Column(String, default="active")

    student = relationship("Student", back_populates="debts")
    plan_items = relationship("IndividualPlanItem", back_populates="debt", cascade="all, delete-orphan")


class AttestationItem(Base):
    __tablename__ = "attestation_items"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    discipline_name = Column(String, nullable=False)
    credits = Column(Integer, nullable=True)
    control_form = Column(String, nullable=True)
    result = Column(String, nullable=True)
    attestation_type = Column(String, nullable=True)

    student = relationship("Student", back_populates="attestation_items")


class IndividualPlanItem(Base):
    __tablename__ = "individual_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    debt_id = Column(Integer, ForeignKey("debts.id", ondelete="CASCADE"), nullable=True)
    discipline_name = Column(String, nullable=False)
    hours = Column(Integer, nullable=True)
    credits = Column(Integer, nullable=True)
    control_form = Column(String, nullable=True)
    deadline = Column(Date, nullable=True)

    student = relationship("Student", back_populates="individual_plan_items")
    debt = relationship("Debt", back_populates="plan_items")