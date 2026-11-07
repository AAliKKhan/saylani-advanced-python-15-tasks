"""
Task 11 | Multi-File Student Gradebook
File handling, dictionaries, exceptions

Problem: Merge students.csv (student_id, name) and scores.csv (student_id,
subject, marks). Calculate per-student average, grade, and rank; export
report.csv.

Requirements:
  - Marks must be 0-100; reject unknown IDs and duplicate student-subject
    entries.
  - Grades: A >= 85, B >= 70, C >= 55, D >= 40, otherwise F.
  - Rank by average, then ID.

Sample / Expected Behavior:
  Student 101 with marks 90, 80, 85 -> average 85.0, grade A.
"""

import csv
import os

STUDENTS_HEADER = ("student_id", "name")
SCORES_HEADER = ("student_id", "subject", "marks")
REPORT_HEADER = ("rank", "student_id", "name", "average", "grade",
                 "subjects")

GRADE_BANDS = ((85, "A"), (70, "B"), (55, "C"), (40, "D"))


def grade_for(average):
    """Map an average mark to a letter grade."""
    for threshold, letter in GRADE_BANDS:
        if average >= threshold:
            return letter
    return "F"


def _parse_id(value, path, row_number):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{path} row {row_number}: invalid student_id "
                         f"{value!r}")


def load_students(path):
    """Return {student_id: name} from students.csv."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"students file not found: {path}")

    students = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("students.csv is empty")
        missing = [c for c in STUDENTS_HEADER if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"students.csv missing columns: {missing}")

        for row_number, row in enumerate(reader, start=2):
            student_id = _parse_id(row.get("student_id"), path, row_number)
            name = (row.get("name") or "").strip()
            if not name:
                raise ValueError(f"{path} row {row_number}: name is empty")
            if student_id in students:
                raise ValueError(f"{path} row {row_number}: duplicate "
                                 f"student_id {student_id}")
            students[student_id] = name
    return students


def load_scores(path, students):
    """Return ({student_id: {subject: marks}}, rejected_rows).

    Rows are rejected (not fatal) when the student is unknown, the marks are
    outside 0-100, or the student/subject pair already exists.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"scores file not found: {path}")

    scores = {student_id: {} for student_id in students}
    rejected = []

    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("scores.csv is empty")
        missing = [c for c in SCORES_HEADER if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"scores.csv missing columns: {missing}")

        for row_number, row in enumerate(reader, start=2):
            raw_id = (row.get("student_id") or "").strip()
            subject = (row.get("subject") or "").strip()
            raw_marks = (row.get("marks") or "").strip()

            try:
                student_id = _parse_id(raw_id, path, row_number)
            except ValueError as exc:
                rejected.append((row, str(exc)))
                continue

            if student_id not in students:
                rejected.append((row, f"unknown student_id {student_id}"))
                continue
            if not subject:
                rejected.append((row, "subject is empty"))
                continue
            try:
                marks = float(raw_marks)
            except ValueError:
                rejected.append((row, f"marks must be a number, "
                                      f"got {raw_marks!r}"))
                continue
            if not 0 <= marks <= 100:
                rejected.append((row, f"marks must be between 0 and 100, "
                                      f"got {raw_marks}"))
                continue
            if subject in scores[student_id]:
                rejected.append((row, f"duplicate subject {subject!r} for "
                                      f"student {student_id}"))
                continue

            scores[student_id][subject] = marks

    return scores, rejected


def build_report(students, scores):
    """Return the ranked report rows.

    Ordering: average descending, then student_id ascending. The rank is the
    position in that ordering (1-based).
    """
    rows = []
    for student_id, name in students.items():
        marks = scores.get(student_id, {})
        if marks:
            average = round(sum(marks.values()) / len(marks), 2)
        else:
            average = 0.0
        rows.append({
            "student_id": student_id,
            "name": name,
            "average": average,
            "grade": grade_for(average),
            "subjects": len(marks),
        })

    rows.sort(key=lambda r: (-r["average"], r["student_id"]))
    for position, row in enumerate(rows, start=1):
        row["rank"] = position
    return rows


def write_report(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "rank": row["rank"],
                "student_id": row["student_id"],
                "name": row["name"],
                "average": f'{row["average"]:.2f}',
                "grade": row["grade"],
                "subjects": row["subjects"],
            })


def generate_report(students_path, scores_path, report_path):
    """Merge both CSVs and export report.csv.

    Returns (rows, rejected) so callers can inspect rejected score rows.
    """
    students = load_students(students_path)
    scores, rejected = load_scores(scores_path, students)
    rows = build_report(students, scores)
    write_report(report_path, rows)
    return rows, rejected


def write_sample_data(students_path, scores_path):
    """Generate the sample CSV files used by this task."""
    with open(students_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(STUDENTS_HEADER)
        writer.writerow([101, "Ali"])
        writer.writerow([102, "Sara"])
        writer.writerow([103, "Hina"])

    with open(scores_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(SCORES_HEADER)
        writer.writerow([101, "Math", 90])
        writer.writerow([101, "English", 80])
        writer.writerow([101, "Science", 85])
        writer.writerow([102, "Math", 75])
        writer.writerow([102, "English", 65])
        writer.writerow([103, "Math", 45])
        writer.writerow([103, "Science", 50])
        writer.writerow([999, "Math", 88])      # rejected: unknown id
        writer.writerow([102, "Math", 99])      # rejected: duplicate subject
        writer.writerow([103, "English", 150])  # rejected: marks > 100
        writer.writerow([103, "English", -5])   # rejected: marks < 0
    return students_path, scores_path


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        students_csv = os.path.join(folder, "students.csv")
        scores_csv = os.path.join(folder, "scores.csv")
        report_csv = os.path.join(folder, "report.csv")

        write_sample_data(students_csv, scores_csv)
        rows, rejected = generate_report(students_csv, scores_csv, report_csv)

        by_id = {row["student_id"]: row for row in rows}
        assert by_id[101]["average"] == 85.0, by_id[101]
        assert by_id[101]["grade"] == "A"
        assert len(rejected) == 4, rejected

        # Rank order: 101 (85.0) > 102 (70.0) > 103 (47.5)
        assert [row["student_id"] for row in rows] == [101, 102, 103]
        assert by_id[101]["rank"] == 1

        with open(report_csv, encoding="utf-8") as handle:
            content = handle.read()
        assert "1,101,Ali,85.00,A,3" in content
        print(content)
    print("all sample cases passed")
