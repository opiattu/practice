from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db
import models
import crud
import schemas
from excel_parser import ExcelDataLoader

UPLOAD_DIR = Path(__file__).parent / "uploads"


@asynccontextmanager
async def lifespan(_: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    UPLOAD_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="EduTrack API", lifespan=lifespan)

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


@app.get("/students", response_model=list[schemas.StudentResponse])
def get_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_students(db, skip=skip, limit=limit)


@app.get("/students/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise HTTPException(status_code=404, detail="Студент не найден")
    return {"message": "Студент удалён"}


@app.get("/students/{student_id}/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard(student_id: int, db: Session = Depends(get_db)):
    data = crud.get_dashboard_data(db, student_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return data


@app.post("/students/{student_id}/create-plan")
def create_plan(student_id: int, db: Session = Depends(get_db)):
    if crud.get_student(db, student_id) is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return {"message": "План сформирован"}


@app.patch("/plan-items/{item_id}", response_model=schemas.PlanItemResponse)
def patch_plan_item(item_id: int, body: schemas.PlanItemUpdate, db: Session = Depends(get_db)):
    item = crud.update_plan_item(db, item_id, body.model_dump(exclude_none=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Запись плана не найдена")
    return item


@app.post("/upload-excel", response_model=schemas.UploadResponse)
async def upload_excel(
    file: UploadFile = File(...),
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    safe_name = Path(file.filename or "upload.xlsx").name
    if not safe_name or safe_name in {".", ".."}:
        safe_name = "upload.xlsx"

    file_path = UPLOAD_DIR / safe_name
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = ExcelDataLoader(db).save_to_database(str(file_path), student_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Ошибка обработки файла"))

    return schemas.UploadResponse(
        message="Файл успешно загружен и обработан",
        student_id=result["student_id"],
        disciplines_loaded=result["disciplines_count"],
        debts_loaded=result["debts_count"],
        plan_items_loaded=result["plan_items_count"],
    )
