import os
import openpyxl
from datetime import date


class ExcelParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(file_path, data_only=True)

    def _clean(self, value):
        if value is None:
            return ""
        return str(value).replace("\r", "").strip()

    def _get_filename_parts(self):
        filename = os.path.basename(self.file_path)
        name = os.path.splitext(filename)[0]
        return name.split("_")

    def _get_student_card_from_filename(self):
        parts = self._get_filename_parts()
        if parts and parts[0].isdigit():
            return parts[0]
        return str(abs(hash(os.path.basename(self.file_path))))[:8]

    def _get_group_from_filename(self):
        parts = self._get_filename_parts()
        # 028_Марденгский_Кирилл_Александрович_141а_ПИо_...
        if len(parts) >= 6:
            return f"{parts[4]}-{parts[5]}"
        if len(parts) >= 5:
            return parts[4]
        return "Не указана"

    def _get_full_name_from_filename(self):
        parts = self._get_filename_parts()
        if len(parts) >= 4:
            return f"{parts[1]} {parts[2]} {parts[3]}"
        return "Неизвестный студент"

    def parse_student_info(self):
        sheet = self.workbook["Титул"] if "Титул" in self.workbook.sheetnames else self.workbook.active

        full_name = ""

        # 1. Основной вариант: H27
        try:
            raw_name = sheet["H27"].value
            full_name = self._clean(raw_name)
            if full_name:
                lines = [line.strip() for line in full_name.split("\n") if line.strip()]
                if lines:
                    full_name = lines[-1]
        except Exception:
            full_name = ""

        # 2. Запасной вариант: если в Excel не нашли — берём из имени файла
        if not full_name:
            full_name = self._get_full_name_from_filename()

        group_name = self._get_group_from_filename()

        # Направление
        program_name = ""
        try:
            raw_program = sheet["D29"].value
            program_name = self._clean(raw_program)
            if program_name and " " in program_name:
                parts = program_name.split(" ", 1)
                if len(parts) == 2:
                    program_name = parts[1].strip()
        except Exception:
            program_name = ""

        if not program_name:
            program_name = "Не указано"

        # Профиль
        specialization = ""
        try:
            raw_specialization = sheet["D30"].value
            specialization = self._clean(raw_specialization)
        except Exception:
            specialization = ""

        if not specialization:
            specialization = "Не указано"

        student_info = {
            "full_name": full_name,
            "student_card_number": self._get_student_card_from_filename(),
            "group_name": group_name,
            "course": 4,
            "program_name": program_name,
            "specialization": specialization,
        }

        print("PARSED STUDENT INFO:", student_info)
        return student_info

    def parse_attested_items(self):
        if "Переаттестация" not in self.workbook.sheetnames:
            return []

        sheet = self.workbook["Переаттестация"]
        items = []
        current_name = None

        for row in range(4, sheet.max_row + 1):
            name_val = sheet.cell(row=row, column=2).value
            credits_val = sheet.cell(row=row, column=7).value
            control_form = sheet.cell(row=row, column=9).value
            attestation_type = sheet.cell(row=row, column=10).value
            result_val = sheet.cell(row=row, column=11).value

            if name_val:
                current_name = self._clean(name_val)

            if not current_name:
                continue

            if not attestation_type and not result_val and not control_form:
                continue

            items.append({
                "discipline_name": current_name,
                "credits": int(float(credits_val)) if credits_val else 0,
                "control_form": self._clean(control_form) or "Не указано",
                "result": self._clean(result_val) or "Не указано",
                "attestation_type": self._clean(attestation_type) or "Не указано",
            })

        return items

    def parse_plan_items(self):
        if "План" not in self.workbook.sheetnames:
            return []

        sheet = self.workbook["План"]
        items = []

        for row in range(6, sheet.max_row + 1):
            name_val = sheet.cell(row=row, column=3).value
            if not name_val:
                continue

            name = self._clean(name_val)
            if not name:
                continue

            lowered = name.lower()
            if lowered.startswith("модуль") or "блок" in lowered or "часть" in lowered:
                continue

            exam = sheet.cell(row=row, column=4).value
            credit = sheet.cell(row=row, column=5).value
            credit_with_mark = sheet.cell(row=row, column=6).value
            course_work = sheet.cell(row=row, column=7).value

            credits_val = sheet.cell(row=row, column=8).value
            hours_val = sheet.cell(row=row, column=9).value

            credits = int(float(credits_val)) if credits_val else 0
            hours = int(float(hours_val)) if hours_val else 0

            control_form = "Не указано"
            if exam:
                control_form = "Экзамен"
            elif credit:
                control_form = "Зачет"
            elif credit_with_mark:
                control_form = "Зачет с оценкой"
            elif course_work:
                control_form = "Курсовая работа"

            items.append({
                "discipline_name": name,
                "hours": hours,
                "credits": credits,
                "control_form": control_form,
            })

        return items

    def parse_debts(self):
        plan_items = self.parse_plan_items()
        attested_items = self.parse_attested_items()

        attested_names = {
            self._clean(item["discipline_name"]).lower()
            for item in attested_items
            if item.get("discipline_name")
        }

        debts = []
        for item in plan_items:
            name = self._clean(item["discipline_name"])
            if not name:
                continue

            if name.lower() in attested_names:
                continue

            debts.append({
                "name": name,
                "remaining_credits": item["credits"],
                "remaining_hours": item["hours"],
                "control_form": item.get("control_form", "Не указано"),
                "deadline": None,
            })

        return debts


class ExcelDataLoader:
    def __init__(self, db_session):
        self.db = db_session

    def save_to_database(self, file_path: str, student_id: int = None):
        from models import Student, Debt, AttestationItem, IndividualPlanItem

        try:
            parser = ExcelParser(file_path)
            student_info = parser.parse_student_info()

            card = student_info["student_card_number"]

            db_student = None
            if student_id:
                db_student = self.db.query(Student).filter(Student.id == student_id).first()

            if not db_student:
                db_student = self.db.query(Student).filter(
                    Student.student_card_number == card
                ).first()

            if db_student:
                db_student.full_name = student_info["full_name"]
                db_student.group_name = student_info["group_name"]
                db_student.course = student_info["course"]
                db_student.program_name = student_info["program_name"]
                db_student.specialization = student_info["specialization"]
                db_student.status = "active"
            else:
                db_student = Student(
                    full_name=student_info["full_name"],
                    student_card_number=card,
                    group_name=student_info["group_name"],
                    course=student_info["course"],
                    program_name=student_info["program_name"],
                    specialization=student_info["specialization"],
                    status="active",
                )
                self.db.add(db_student)
                self.db.flush()

            new_student_id = db_student.id

            # Очищаем старые данные этого студента
            self.db.query(IndividualPlanItem).filter(
                IndividualPlanItem.student_id == new_student_id
            ).delete(synchronize_session=False)

            self.db.query(AttestationItem).filter(
                AttestationItem.student_id == new_student_id
            ).delete(synchronize_session=False)

            self.db.query(Debt).filter(
                Debt.student_id == new_student_id
            ).delete(synchronize_session=False)

            # Переаттестации
            attested_items = parser.parse_attested_items()
            for item in attested_items:
                self.db.add(
                    AttestationItem(
                        student_id=new_student_id,
                        discipline_name=item["discipline_name"],
                        credits=item["credits"],
                        control_form=item["control_form"],
                        result=item["result"],
                        attestation_type=item["attestation_type"],
                    )
                )

            # Долги
            debts = parser.parse_debts()
            created_debts = []

            for item in debts:
                debt = Debt(
                    student_id=new_student_id,
                    discipline_name=item["name"],
                    hours_remaining=item["remaining_hours"],
                    credits_remaining=item["remaining_credits"],
                    reassessment_deadline=item.get("deadline"),
                    status="active",
                )
                self.db.add(debt)
                self.db.flush()
                created_debts.append(debt)

            # Индивидуальный план
            for idx, item in enumerate(debts):
                linked_debt_id = created_debts[idx].id if idx < len(created_debts) else None
                self.db.add(
                    IndividualPlanItem(
                        student_id=new_student_id,
                        debt_id=linked_debt_id,
                        discipline_name=item["name"],
                        hours=item["remaining_hours"],
                        credits=item["remaining_credits"],
                        control_form=item.get("control_form", "Не указано"),
                        deadline=item.get("deadline"),
                    )
                )

            self.db.commit()

            return {
                "success": True,
                "student_id": new_student_id,
                "plan_id": None,
                "student_info": student_info,
                "disciplines_count": len(attested_items),
                "debts_count": len(debts),
                "plan_items_count": len(debts),
                "errors": [],
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "student_id": None,
                "plan_id": None,
                "student_info": None,
                "disciplines_count": 0,
                "debts_count": 0,
                "plan_items_count": 0,
                "errors": [str(e)],
            }