"""Synthetic district generator — realistic fake data, never real student records.

Produces a deterministic (seeded) district: several schools, dozens of caseloads
across varied IDEA disability categories, IEP deadlines with **deliberately seeded
timeline violations** (overdue + due-soon), and a few **messy source documents**
for the Evidence Ingestor to normalize.

    python -m casesentinel.data.generate        # writes fixtures/district.json

All data is synthetic. See README / PROJECT.md — for this domain, synthetic-only
is a maturity signal, not a limitation.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

AS_OF = date(2026, 8, 29)  # "today" for the demo; drift is computed relative to this
SEED = 42
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "district.json"

# The 13 IDEA disability categories.
DISABILITY_CATEGORIES = [
    "Specific Learning Disability",
    "Speech or Language Impairment",
    "Other Health Impairment",
    "Autism",
    "Intellectual Disability",
    "Emotional Disturbance",
    "Developmental Delay",
    "Multiple Disabilities",
    "Hearing Impairment",
    "Orthopedic Impairment",
    "Visual Impairment",
    "Traumatic Brain Injury",
    "Deaf-Blindness",
]

SCHOOL_NAMES = [
    "Maple Grove Elementary",
    "Riverside Middle School",
    "Cedar Hills High School",
    "Lincoln K-8 Academy",
]

FIRST_NAMES = [
    "Jordan", "Riley", "Avery", "Casey", "Morgan", "Taylor", "Jamie", "Quinn",
    "Skyler", "Devon", "Harper", "Rowan", "Emery", "Sawyer", "Reese", "Parker",
    "Elliot", "Nadia", "Malik", "Priya", "Diego", "Aisha", "Leo", "Mei",
    "Omar", "Sofia", "Theo", "Zara", "Ivan", "Lucia", "Kai", "Nora",
    "Amara", "Ben", "Chloe", "Dante", "Ella", "Finn", "Gia", "Hugo",
]
LAST_NAMES = [
    "Rivera", "Chen", "Okafor", "Nguyen", "Patel", "Garcia", "Johnson", "Kim",
    "Alvarez", "Brooks", "Silva", "Haddad", "Rossi", "Novak", "Mensah", "Reyes",
]
STAFF_NAMES = [
    "Ms. Alvarez", "Mr. Brooks", "Ms. Chen", "Mr. Delgado", "Ms. Evans",
    "Mr. Fisher", "Ms. Gupta", "Mr. Hughes",
]


@dataclass
class School:
    id: str
    name: str


@dataclass
class Staff:
    id: str
    name: str
    role: str
    school_id: str


@dataclass
class Student:
    id: str
    first_name: str
    last_name: str
    dob: str
    grade: int
    school_id: str
    disability_category: str
    case_manager_id: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Case:
    student_id: str
    # ISO dates; null where not applicable (e.g. transition plan under age 16).
    annual_review_due: str
    reevaluation_due: str
    initial_evaluation_due: str | None
    transition_plan_due: str | None
    seeded_status: str  # compliant | due_soon | overdue (the intended drift)


@dataclass
class Document:
    id: str
    student_id: str
    type: str
    author: str
    date: str
    text: str


@dataclass
class District:
    name: str
    as_of: str
    schools: list[School] = field(default_factory=list)
    staff: list[Staff] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)


# Messy source-document templates (typos, shorthand, mixed content) keyed by type.
_DOC_TEMPLATES = {
    "progress_note": (
        "{md} - {first} worked on reading fluency, got abt {wpm} wpm today, still "
        "struggles w/ multisyllabic words. behavior ok mostly. parent emailed re: "
        "homework??? need to follow up. accommodations seemed to help. -{author}"
    ),
    "therapy_memo": (
        "Session {md}. {first} — artic /r/ and /s/ blends, ~{pct}% accuracy in "
        "structured tasks, carryover inconsistent in convo. recommend continue 2x30. "
        "note: missed last wk (absent). {author}"
    ),
    "behavior_log": (
        "{md} incident log: {first} left seat 4x during math, 1 verbal refusal, "
        "redirected w/ break card - worked. no aggression. antecedent = task demand "
        "(worksheets). fyi running low on break passes. -{author}"
    ),
}


def _iso(d: date) -> str:
    return d.isoformat()


def generate_district(as_of: date = AS_OF, seed: int = SEED) -> District:
    rng = random.Random(seed)
    district = District(name="Willow Creek Unified School District", as_of=_iso(as_of))

    schools = [School(id=f"sch-{i+1}", name=n) for i, n in enumerate(SCHOOL_NAMES)]
    district.schools = schools

    staff = [
        Staff(id=f"cm-{i+1}", name=n, role="Case Manager",
              school_id=rng.choice(schools).id)
        for i, n in enumerate(STAFF_NAMES)
    ]
    district.staff = staff

    # ~40 students across the caseloads.
    used_names: set[str] = set()
    n_students = 40
    overdue_target, due_soon_target = 8, 10

    for i in range(n_students):
        while True:
            fn, ln = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            if f"{fn} {ln}" not in used_names:
                used_names.add(f"{fn} {ln}")
                break
        cm = rng.choice(staff)
        grade = rng.randint(1, 12)
        age = grade + 6
        dob = date(as_of.year - age, rng.randint(1, 12), rng.randint(1, 28))
        student = Student(
            id=f"stu-{i+1:03d}",
            first_name=fn,
            last_name=ln,
            dob=_iso(dob),
            grade=grade,
            school_id=cm.school_id,
            disability_category=rng.choice(DISABILITY_CATEGORIES),
            case_manager_id=cm.id,
        )
        district.students.append(student)

        # Decide the intended drift status for this case.
        if i < overdue_target:
            status = "overdue"
        elif i < overdue_target + due_soon_target:
            status = "due_soon"
        else:
            status = "compliant"

        if status == "overdue":
            annual = as_of - timedelta(days=rng.randint(5, 40))
        elif status == "due_soon":
            annual = as_of + timedelta(days=rng.randint(1, 25))
        else:
            annual = as_of + timedelta(days=rng.randint(60, 300))

        reeval = annual + timedelta(days=rng.randint(200, 700))
        # A few students still awaiting an initial evaluation (60-day clock).
        initial = None
        if rng.random() < 0.15:
            initial = _iso(as_of + timedelta(days=rng.randint(-10, 40)))
        # Transition plan required at age 16+.
        transition = _iso(annual) if age >= 16 else None

        district.cases.append(
            Case(
                student_id=student.id,
                annual_review_due=_iso(annual),
                reevaluation_due=_iso(reeval),
                initial_evaluation_due=initial,
                transition_plan_due=transition,
                seeded_status=status,
            )
        )

    # A handful of messy documents tied to specific students (for Evidence Ingestor).
    doc_students = district.students[:6]
    for j, stu in enumerate(doc_students):
        dtype = list(_DOC_TEMPLATES)[j % len(_DOC_TEMPLATES)]
        author = next(s.name for s in staff if s.id == stu.case_manager_id)
        d = as_of - timedelta(days=rng.randint(3, 20))
        text = _DOC_TEMPLATES[dtype].format(
            md=d.strftime("%-m/%-d"),
            first=stu.first_name,
            wpm=rng.randint(45, 80),
            pct=rng.randint(60, 90),
            author=author,
        )
        district.documents.append(
            Document(id=f"doc-{j+1:03d}", student_id=stu.id, type=dtype,
                     author=author, date=_iso(d), text=text)
        )

    return district


def to_dict(district: District) -> dict:
    d = asdict(district)
    return d


def write_fixture(path: Path = FIXTURE_PATH) -> Path:
    district = generate_district()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(district), indent=2), encoding="utf-8")
    return path


def load_district(path: Path = FIXTURE_PATH) -> dict:
    """Load the committed fixture, generating it on first use if missing."""
    if not path.exists():
        write_fixture(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _summary(d: dict) -> str:
    overdue = sum(1 for c in d["cases"] if c["seeded_status"] == "overdue")
    due_soon = sum(1 for c in d["cases"] if c["seeded_status"] == "due_soon")
    return (
        f"{d['name']} (as of {d['as_of']}): "
        f"{len(d['schools'])} schools, {len(d['staff'])} case managers, "
        f"{len(d['students'])} students, {len(d['documents'])} messy docs; "
        f"seeded drift: {overdue} overdue, {due_soon} due-soon."
    )


def main() -> None:
    path = write_fixture()
    print(f"Wrote {path}")
    print(_summary(load_district(path)))


if __name__ == "__main__":
    main()
