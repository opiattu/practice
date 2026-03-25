from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil

from database import engine, get_db
import models
import crud
from excel_parser import ExcelDataLoader

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="EduTrack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API работает"}


@app.get("/students")
def get_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    students = crud.get_all_students(db, skip=skip, limit=limit)
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "student_card_number": s.student_card_number,
            "group_name": s.group_name,
            "course": s.course,
            "program_name": s.program_name,
            "specialization": s.specialization,
            "status": s.status,
        }
        for s in students
    ]


@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    return {
        "id": student.id,
        "full_name": student.full_name,
        "student_card_number": student.student_card_number,
        "group_name": student.group_name,
        "course": student.course,
        "program_name": student.program_name,
        "specialization": student.specialization,
        "status": student.status,
    }


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_student(db, student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return {"message": "Студент удалён"}


@app.get("/students/{student_id}/dashboard")
def get_dashboard(student_id: int, db: Session = Depends(get_db)):
    data = crud.get_dashboard_data(db, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return data


@app.get("/students/{student_id}/report")
def get_report(student_id: int, db: Session = Depends(get_db)):
    data = crud.create_report_data(db, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return data


@app.post("/students/{student_id}/create-plan")
def create_plan(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return {"message": "План сформирован"}


@app.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    student_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    loader = ExcelDataLoader(db)
    result = loader.save_to_database(file_path, student_id)

    if result.get("success"):
        return {
            "message": "Файл успешно загружен и обработан",
            "student_id": result.get("student_id"),
            "plan_id": result.get("plan_id"),
            "disciplines_loaded": result.get("disciplines_count", 0),
            "debts_loaded": result.get("debts_count", 0),
            "plan_items_loaded": result.get("plan_items_count", 0),
        }

    raise HTTPException(
        status_code=400,
        detail=result.get("errors", ["Ошибка обработки файла"])
    )
