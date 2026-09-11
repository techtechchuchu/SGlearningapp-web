"""Business functions extracted without UI/startup side effects. Source f84b11cadac077ae3a056528b3ae27a00e0db57c. See docs/feature-parity.md."""

import io, base64, re, hashlib, html

from collections import Counter

from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from pathlib import Path

import pandas as pd

from .database import database as supabase

from .context import st

BOOKS = [
    "공통수학2 고쟁이",
    "공통수학2 RPM",
    "미적분1 고쟁이",
    "확통 고쟁이",
    "미적분2 쎈",
    "X-패턴 미적분2",
    "기하 쎈",
    "마플교과서 공통수학1",
    "공통수학1 RPM"
]

TEACHERS = ["이주백.T", "박병민.T", "노대근.T"]

ALL_TEACHER_ADMIN = "전체 관리자"

XPATTERN_SCHOOL_MAP = {
    "X-패턴 공통수학2": {
        "24 강남고": [{"offset": 500, "max": 25, "exam_type": '1학기기말'}],
        "24 다운고": [{"offset": 600, "max": 16, "exam_type": '1학기기말'}],
        "24 달천고": [{"offset": 700, "max": 31, "exam_type": '1학기기말'}],
        "23 달천고": [{"offset": 2800, "max": 38, "exam_type": ''}],
        "24 동천고": [{"offset": 800, "max": 38, "exam_type": '1학기기말'}],
        "24 무거고": [{"offset": 900, "max": 34, "exam_type": '1학기기말'}],
        "24 무룡고": [{"offset": 1000, "max": 20, "exam_type": '2학기중간'}],
        "24 성신고": [{"offset": 1100, "max": 30, "exam_type": '1학기기말'}],
        "24 신정고": [{"offset": 1200, "max": 35, "exam_type": '1학기기말'}],
        "24 가온고+매곡고": [{"offset": 1300, "max": 20, "exam_type": '1학기기말'}],
        "24 중앙고+천상고": [{"offset": 1400, "max": 20, "exam_type": '1학기기말'}],
        "24 울산여고": [{"offset": 1500, "max": 20, "exam_type": '1학기기말'}],
        "23 울산여고": [{"offset": 3100, "max": 27, "exam_type": ''}],
        "24 제일고": [{"offset": 1600, "max": 20, "exam_type": '1학기기말'}],
        "24 우신고": [{"offset": 1700, "max": 20, "exam_type": '1학기기말'}],
        "24 성광여고": [{"offset": 1800, "max": 20, "exam_type": '1학기기말'}],
        "23 성광여고": [{"offset": 2900, "max": 16, "exam_type": ''}],
        "24 신선여고": [{"offset": 1900, "max": 20, "exam_type": '1학기기말'}],
        "24 대현고": [{"offset": 2000, "max": 20, "exam_type": '1학기기말'}],
        "24 삼산고": [{"offset": 2100, "max": 20, "exam_type": '1학기기말'}],
        "24 학성고": [{"offset": 2200, "max": 20, "exam_type": '1학기기말'}],
        "24 범서고+현대고": [{"offset": 2300, "max": 20, "exam_type": '1학기기말'}],
        "24 울산외고": [{"offset": 2400, "max": 20, "exam_type": '1학기기말'}],
        "23 울산외고": [{"offset": 3200, "max": 7, "exam_type": ''}],
        "24 울산고": [{"offset": 2500, "max": 20, "exam_type": '1학기기말'}],
        "23 울산고": [{"offset": 3008, "max": 20, "exam_type": ''}],
        "24 함월고": [{"offset": 2600, "max": 20, "exam_type": '1학기기말'}],
        "24 약사고": [{"offset": 2700, "max": 20, "exam_type": '1학기기말'}],
        "23 천상고+학성고+학성여고": [{"offset": 3300, "max": 68, "exam_type": '(내신기출, 여러 학교 뒤섞임)'}],
    },
    "X-패턴 미적분1": {
        "23 매곡고": [{"offset": 500, "max": 18, "exam_type": '2학기중간'}],
        "23 성광여고": [{"offset": 600, "max": 22, "exam_type": '2학기중간'}],
        "24 성광여고": [{"offset": 2900, "max": 22, "exam_type": '2학기중간'}],
        "23 신정고": [{"offset": 700, "max": 23, "exam_type": '1학기중간'}],
        "24 신정고": [{"offset": 2600, "max": 21, "exam_type": '2학기중간'}],
        "23 울산고": [{"offset": 800, "max": 15, "exam_type": '1학기중간'}],
        "23 울산여고": [{"offset": 900, "max": 18, "exam_type": '1학기중간'}],
        "24 울산여고": [{"offset": 2300, "max": 20, "exam_type": '1학기중간'}],
        "23 울산외고": [{"offset": 1000, "max": 21, "exam_type": '2학기중간'}],
        "24 울산외고": [{"offset": 2200, "max": 20, "exam_type": '2학기중간'}],
        "23 제일고": [{"offset": 1100, "max": 18, "exam_type": '2학기중간'}],
        "23 천상고": [{"offset": 1200, "max": 22, "exam_type": '1학기중간'}],
        "24 천상고": [{"offset": 1900, "max": 19, "exam_type": '2학기중간'}],
        "23 학성고": [{"offset": 1300, "max": 20, "exam_type": '2학기중간'}],
        "24 학성고": [{"offset": 2000, "max": 18, "exam_type": '2학기중간'}],
        "23 함월고": [{"offset": 1400, "max": 20, "exam_type": '2학기중간'}],
        "24 함월고": [{"offset": 1700, "max": 21, "exam_type": '2학기중간'}],
        "24 화암고": [{"offset": 1500, "max": 21, "exam_type": '2학기중간'}],
        "24 현대고": [{"offset": 1600, "max": 22, "exam_type": '2학기중간'}],
        "24 학성여고": [{"offset": 1816, "max": 4, "exam_type": '2학기중간'}],
        "24 중앙여고": [{"offset": 2115, "max": 5, "exam_type": '2학기중간'}],
        "24 약사고": [{"offset": 2400, "max": 21, "exam_type": '2학기중간'}],
        "24 우신고": [{"offset": 2500, "max": 20, "exam_type": '2학기중간'}],
        "24 신선여고": [{"offset": 2700, "max": 22, "exam_type": '2학기중간'}],
        "24 성신고": [{"offset": 2800, "max": 23, "exam_type": '2학기중간'}],
        "24 삼산고": [{"offset": 3000, "max": 21, "exam_type": '1학기중간'}],
        "24 범서고": [{"offset": 3100, "max": 22, "exam_type": '2학기중간'}],
        "24 무룡고": [{"offset": 3200, "max": 19, "exam_type": '2학기중간'}],
        "24 문수고": [{"offset": 3300, "max": 20, "exam_type": '2학기중간'}],
        "24 동천고": [{"offset": 3400, "max": 23, "exam_type": '2학기중간'}],
        "24 무거고": [{"offset": 3500, "max": 24, "exam_type": '2학기중간'}],
        "24 달천고": [{"offset": 3600, "max": 21, "exam_type": '1학기중간'}],
        "24 대송고": [{"offset": 3700, "max": 20, "exam_type": '2학기중간'}],
        "24 남창고": [{"offset": 3800, "max": 22, "exam_type": '2학기중간'}],
    },
    "X-패턴 미적분2": {
        # 원본 Contents의 연도 표기는 한 해씩 밀려 있으므로 본문 실제 시험 연도를 기준으로 함.
        # 2025: PDF 첫 묶음(Contents의 2024 영역), 원본 순서대로 500~1700번대 배정
        "25 강남고": [{"offset": 500, "max": 18, "exam_type": '1학기중간'}],
        "25 다운고": [{"offset": 600, "max": 20, "exam_type": '1학기중간'}],
        "25 대현고": [{"offset": 700, "max": 16, "exam_type": '1학기중간'}],
        "25 무거고": [{"offset": 800, "max": 22, "exam_type": '1학기중간'}],
        "25 성광여고": [{"offset": 900, "max": 20, "exam_type": '1학기중간'}],
        "25 성신고": [{"offset": 1000, "max": 22, "exam_type": '1학기중간'}],
        "25 신정고": [{"offset": 1100, "max": 24, "exam_type": '1학기중간'}],
        "25 우신고": [{"offset": 1200, "max": 20, "exam_type": '1학기중간'}],
        "25 울산고": [{"offset": 1300, "max": 24, "exam_type": '2학기중간'}],
        "25 울산여고": [{"offset": 1400, "max": 23, "exam_type": '2학기중간'}],
        "25 중앙고": [{"offset": 1500, "max": 20, "exam_type": '2학기중간'}],
        "25 천상고": [{"offset": 1600, "max": 20, "exam_type": '1학기중간'}],
        "25 학성고": [{"offset": 1700, "max": 20, "exam_type": '1학기중간'}],

        # 2024: PDF 두 번째 묶음(Contents의 2023 영역), 원본 순서대로 1800~2900번대 배정
        "24 강남고": [
            {"offset": 1800, "max": 20, "exam_type": '2학기중간'},
            {"offset": 1900, "max": 20, "exam_type": '1학기중간'},
        ],
        "24 무거고": [{"offset": 2000, "max": 22, "exam_type": '1학기중간'}],
        "24 삼산고": [{"offset": 2100, "max": 16, "exam_type": '2학기중간'}],
        "24 성광여고": [{"offset": 2200, "max": 20, "exam_type": '1학기중간'}],
        "24 성신고": [{"offset": 2300, "max": 17, "exam_type": '1학기중간'}],
        "24 우신고": [{"offset": 2400, "max": 19, "exam_type": '1학기중간'}],
        "24 울산고": [{"offset": 2500, "max": 20, "exam_type": '2학기중간'}],
        "24 울산여고": [{"offset": 2600, "max": 21, "exam_type": '2학기중간'}],
        "24 중앙고": [{"offset": 2700, "max": 20, "exam_type": '2학기중간'}],
        "24 학성고": [{"offset": 2800, "max": 20, "exam_type": '1학기중간'}],
        "24 함월고": [{"offset": 2900, "max": 20, "exam_type": '1학기중간'}],
    },
    "X-패턴 확통": {
        # 2024: 원본 PDF Contents 순서대로 500~3200번대 배정
        "24 강남고": [{"offset": 500, "max": 19, "exam_type": '1학기중간'}],
        "24 다운고": [{"offset": 600, "max": 22, "exam_type": '1학기중간'}],
        "24 달천고": [{"offset": 700, "max": 21, "exam_type": '2학기중간'}],
        "24 대송고": [{"offset": 800, "max": 19, "exam_type": '2학기중간'}],
        "24 매곡고": [{"offset": 900, "max": 22, "exam_type": '1학기중간'}],
        "24 무거고": [{"offset": 1000, "max": 23, "exam_type": '1학기중간'}],
        "24 무룡고": [{"offset": 1100, "max": 21, "exam_type": '2학기중간'}],
        "24 삼산고": [{"offset": 1200, "max": 22, "exam_type": '2학기중간'}],
        "24 성광여고": [{"offset": 1300, "max": 19, "exam_type": '1학기중간'}],
        "24 신선여고": [{"offset": 1400, "max": 21, "exam_type": '1학기중간'}],
        "24 약사고": [{"offset": 1500, "max": 20, "exam_type": '1학기중간'}],
        "24 우신고": [
            {"offset": 1600, "max": 20, "exam_type": '1학기중간'},
            {"offset": 1700, "max": 20, "exam_type": '2학기중간'},
        ],
        "24 울산고": [{"offset": 1800, "max": 24, "exam_type": '2학기중간'}],
        "24 울산여고": [{"offset": 1900, "max": 24, "exam_type": '2학기중간'}],
        "24 울산외고": [{"offset": 2000, "max": 18, "exam_type": '1학기중간'}],
        "24 제일고": [{"offset": 2100, "max": 22, "exam_type": '1학기중간'}],
        "24 중앙고": [{"offset": 2200, "max": 24, "exam_type": '2학기중간'}],
        "24 천상고": [{"offset": 2300, "max": 21, "exam_type": '2학기중간'}],
        "24 학성고": [
            {"offset": 2400, "max": 20, "exam_type": '1학기중간'},
            {"offset": 2500, "max": 20, "exam_type": '2학기중간'},
        ],
        "24 학성여고": [{"offset": 2600, "max": 19, "exam_type": '1학기중간'}],
        "24 현대고": [
            {"offset": 2700, "max": 22, "exam_type": '1학기중간'},
            {"offset": 2800, "max": 22, "exam_type": '2학기중간'},
        ],
        "24 호계고": [{"offset": 2900, "max": 20, "exam_type": '1학기중간'}],
        "24 화봉고": [{"offset": 3000, "max": 22, "exam_type": '2학기중간'}],
        "24 화암고": [{"offset": 3100, "max": 19, "exam_type": '1학기중간'}],
        "24 효정고": [{"offset": 3200, "max": 22, "exam_type": '1학기중간'}],

        # 2023: 원본 PDF Contents 순서대로 3300~4000번대 배정
        "23 삼산고": [{"offset": 3300, "max": 21, "exam_type": '2학기중간'}],
        "23 울산고": [{"offset": 3400, "max": 16, "exam_type": '2학기중간'}],
        "23 울산여고": [{"offset": 3500, "max": 20, "exam_type": '2학기중간'}],
        "23 울산외고": [{"offset": 3600, "max": 23, "exam_type": '1학기중간'}],
        "23 제일고": [{"offset": 3700, "max": 18, "exam_type": '1학기중간'}],
        "23 학성고": [
            {"offset": 3800, "max": 21, "exam_type": '1학기중간'},
            {"offset": 3900, "max": 21, "exam_type": '2학기중간'},
        ],
        "23 함월고": [{"offset": 4000, "max": 22, "exam_type": '1학기중간'}],
    },
}

def format_xpattern_display_numbers(book: str, problem_str: str) -> str:
    """
    X-패턴 계열은 wrong_answers.problem에 학교별 오프셋이 더해진 내부 번호로
    저장되어 있다(학생이 입력한 원래 시험지 번호가 아님 - build_auto.py PDF 생성이
    이 내부 번호를 그대로 써야 하므로 저장값 자체는 바꾸지 않는다).
    선생님 화면 등 사람이 읽는 표에서는 이 함수로 원래 시험지 번호로 되돌려 보여준다.
    """
    schools = XPATTERN_SCHOOL_MAP.get(book)
    if not schools:
        return problem_str

    groups: dict = {}
    unmatched = []

    for number in parse_problem_numbers(problem_str):
        n = int(number)
        matched_school = None
        matched_original = None

        for school, blocks in schools.items():
            for b in blocks:
                if b["offset"] < n <= b["offset"] + b["max"]:
                    matched_school = school
                    matched_original = n - b["offset"]
                    break
            if matched_school:
                break

        if matched_school:
            groups.setdefault(matched_school, []).append(str(matched_original))
        else:
            unmatched.append(number)

    if not groups:
        return problem_str

    if len(groups) == 1 and not unmatched:
        return ", ".join(next(iter(groups.values())))

    parts = [f"{school}: {', '.join(nums)}" for school, nums in groups.items()]
    if unmatched:
        parts.append("확인필요: " + ", ".join(unmatched))
    return " / ".join(parts)

ROSTER_REQUIRED_COLUMNS = {
    "반명",
    "담당선생님",
    "학생명",
    "학교명",
    "학년",
}

GRADES = ["중3", "고1", "고2", "고3"]

def now_kst_iso() -> str:
    """Supabase timestamp 컬럼에 저장할 한국 시간 문자열입니다."""
    return datetime.now(KST).replace(tzinfo=None).isoformat(timespec="seconds")

def get_active_notices(target: str = "all") -> list[dict]:
    """현재 활성화된 공지를 우선순위 순서로 조회합니다."""
    rows = fetch_all_rows(
        "notices",
        "id,title,content,target,is_active,priority,created_at,updated_at",
        filters=[("is_active", "eq", True)],
        order_column="priority",
        desc=True,
    )

    allowed_targets = {"all", str(target or "all").strip()}
    return [
        row
        for row in rows
        if str(row.get("target", "all")).strip() in allowed_targets
    ]

def get_all_notices_df() -> pd.DataFrame:
    rows = fetch_all_rows(
        "notices",
        "id,title,content,target,is_active,priority,created_at,updated_at",
        order_column="priority",
        desc=True,
    )

    columns = [
        "공지ID", "제목", "내용", "노출대상",
        "사용중", "우선순위", "등록일시", "수정일시",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "공지ID": row.get("id"),
                "제목": row.get("title", ""),
                "내용": row.get("content", ""),
                "노출대상": row.get("target", "all"),
                "사용중": bool(row.get("is_active", True)),
                "우선순위": int(row.get("priority", 0) or 0),
                "등록일시": row.get("created_at", ""),
                "수정일시": row.get("updated_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )

def fetch_all_rows(
    table_name: str,
    columns: str = "*",
    *,
    filters: list[tuple[str, str, object]] | None = None,
    order_column: str | None = None,
    desc: bool = False,
    page_size: int = 1000
) -> list[dict]:
    """PostgREST 행 제한을 고려하여 전체 데이터를 페이지 단위로 가져옵니다."""
    all_rows: list[dict] = []
    start = 0

    while True:
        query = supabase.table(table_name).select(columns)

        for column, operation, value in filters or []:
            if operation == "eq":
                query = query.eq(column, value)
            elif operation == "neq":
                query = query.neq(column, value)
            elif operation == "in":
                query = query.in_(column, value)
            else:
                raise ValueError(f"지원하지 않는 필터 연산입니다: {operation}")

        if order_column:
            query = query.order(order_column, desc=desc)

        response = query.range(start, start + page_size - 1).execute()
        rows = response.data or []
        all_rows.extend(rows)

        if len(rows) < page_size:
            break

        start += page_size

    return all_rows

def normalize_teacher_name(value) -> str:
    """
    담당 선생님 표기의 공백·점·영문 대소문자 차이를 자동 통일합니다.

    예:
    - 노대근T / 노대근.T / 노대근t / 노대근.t → 노대근.T
    - 이주백T / 이주백.T / 이주백t / 이주백.t → 이주백.T
    - 새 선생님도 이름 뒤에 T 또는 t가 있으면 자동으로 '이름.T'로 변환됩니다.
    """
    raw = str(value or "").strip()

    if not raw:
        return ""

    compact = re.sub(r"\s+", "", raw)

    # 이름 뒤의 T, t, .T, .t를 모두 제거한 뒤 표준 '.T'를 붙입니다.
    teacher_match = re.fullmatch(r"(.+?)(?:\.?[Tt])", compact)

    if teacher_match:
        teacher_base = teacher_match.group(1).rstrip(".")
        return f"{teacher_base}.T"

    return raw

def normalize_roster_grade(value) -> str:
    """엑셀의 1, 2, 3 또는 고1, 고2 형식을 앱 학년 형식으로 통일합니다."""
    raw = str(value or "").strip()

    if raw.lower() == "nan" or not raw:
        return "미지정"

    if raw in {"1", "1.0"}:
        return "고1"
    if raw in {"2", "2.0"}:
        return "고2"
    if raw in {"3", "3.0"}:
        return "중3"

    return raw

def get_roster_df() -> pd.DataFrame:
    rows = fetch_all_rows(
        "student_roster",
        "id,class_name,teacher_name,student_name,school_name,grade,book_name,created_at",
        order_column="teacher_name",
        desc=False,
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "기록ID", "반명", "담당선생님", "학생명",
                "학교명", "학년", "매칭교재", "등록일시"
            ]
        )

    return pd.DataFrame(
        [
            {
                "기록ID": row.get("id"),
                "반명": row.get("class_name", ""),
                "담당선생님": normalize_teacher_name(
                    row.get("teacher_name", "")
                ),
                "학생명": row.get("student_name", ""),
                "학교명": row.get("school_name", ""),
                "학년": row.get("grade", ""),
                "매칭교재": row.get("book_name", ""),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ]
    )

def import_roster_from_excel(uploaded_file) -> dict:
    """최종 학생명단 엑셀의 '학생명단' 시트를 Supabase에 일괄 저장합니다."""
    df = pd.read_excel(uploaded_file, sheet_name="학생명단")
    missing = ROSTER_REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            "명단 엑셀에 필요한 열이 없습니다: " + ", ".join(sorted(missing))
        )

    if "매칭교재" not in df.columns:
        df["매칭교재"] = ""

    clean_df = df[
        ["반명", "담당선생님", "학생명", "학교명", "학년", "매칭교재"]
    ].copy()

    for column in ["반명", "담당선생님", "학생명", "학교명", "매칭교재"]:
        clean_df[column] = clean_df[column].fillna("").astype(str).str.strip()

    clean_df["담당선생님"] = clean_df["담당선생님"].apply(
        normalize_teacher_name
    )
    clean_df["학년"] = clean_df["학년"].apply(normalize_roster_grade)
    clean_df = clean_df[
        (clean_df["학생명"] != "")
        & (clean_df["반명"] != "")
        & (clean_df["담당선생님"] != "")
    ].drop_duplicates(
        subset=["반명", "담당선생님", "학생명"]
    )

    rows = [
        {
            "class_name": row["반명"],
            "teacher_name": row["담당선생님"],
            "student_name": row["학생명"],
            "school_name": row["학교명"],
            "grade": row["학년"],
            "book_name": row["매칭교재"],
            "created_at": now_kst_iso(),
        }
        for _, row in clean_df.iterrows()
    ]

    # 명단은 최신 업로드본을 기준으로 전체 교체
    supabase.table("student_roster").delete().neq("id", 0).execute()

    if rows:
        supabase.table("student_roster").insert(rows).execute()

    return {
        "count": len(rows),
        "teachers": sorted(clean_df["담당선생님"].unique().tolist()),
        "classes": sorted(clean_df["반명"].unique().tolist()),
    }

def get_student_roster_rows(username: str) -> pd.DataFrame:
    roster = get_roster_df()

    if roster.empty:
        return roster

    return roster[roster["학생명"] == username].copy()

def get_book_master_df(active_only: bool = True) -> pd.DataFrame:
    filters = [("is_active", "eq", True)] if active_only else []

    rows = fetch_all_rows(
        "book_master",
        (
            "id,book_name,grade,subject,publisher,"
            "question_count,category,is_active,created_at"
        ),
        filters=filters,
        order_column="book_name",
        desc=False,
    )

    columns = [
        "교재ID", "교재명", "학년", "과목", "출판사",
        "문항수", "분류", "사용중", "등록일시",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "교재ID": row.get("id"),
                "교재명": row.get("book_name", ""),
                "학년": row.get("grade", ""),
                "과목": row.get("subject", ""),
                "출판사": row.get("publisher", ""),
                "문항수": row.get("question_count"),
                "분류": row.get("category", "교재"),
                "사용중": bool(row.get("is_active", True)),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )

def get_active_book_names() -> list[str]:
    try:
        book_df = get_book_master_df(active_only=True)

        if not book_df.empty:
            names = (
                book_df["교재명"]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )
            return list(dict.fromkeys(name for name in names if name))
    except Exception:
        pass

    return BOOKS.copy()

def get_student_allowed_books(username: str) -> list[str]:
    """현재 관리자 화면에서 사용 중으로 설정된 교재를 반환합니다."""
    return get_active_book_names()

def split_roster_books(value) -> list[str]:
    """학생 명단의 쉼표 구분 교재 문자열을 개별 교재명으로 분리합니다."""
    raw = str(value or "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(',') if part.strip()]

def get_teacher_student_status_df() -> pd.DataFrame:
    """명단 기준으로 학생별 오답 작성 여부와 문제 개수를 계산합니다."""
    roster = get_roster_df()

    if roster.empty:
        return pd.DataFrame(
            columns=[
                "담당선생님", "반명", "학생명", "학교명",
                "학년", "매칭교재", "작성여부", "작성문제수", "최근작성일시"
            ]
        )

    answer_rows = fetch_all_rows(
        "wrong_answers",
        "username,unit,problem,created_at",
        order_column="id",
        desc=False,
    )

    answer_map: dict[tuple[str, str], dict] = {}

    for row in answer_rows:
        key = (
            str(row.get("username", "")).strip(),
            str(row.get("unit", "")).strip(),
        )
        info = answer_map.setdefault(
            key,
            {"numbers": [], "latest": ""}
        )

        for number in parse_problem_numbers(row.get("problem", "")):
            if number not in info["numbers"]:
                info["numbers"].append(number)

        created_at = str(row.get("created_at", ""))
        if created_at > info["latest"]:
            info["latest"] = created_at

    records = []

    for _, row in roster.iterrows():
        roster_books = split_roster_books(row["매칭교재"]) or [str(row["매칭교재"]).strip()]

        for roster_book in roster_books:
            key = (str(row["학생명"]).strip(), roster_book)
            answer = answer_map.get(key, {"numbers": [], "latest": ""})
            count = len(answer["numbers"])

            records.append(
                {
                    "담당선생님": row["담당선생님"],
                    "반명": row["반명"],
                    "학생명": row["학생명"],
                    "학교명": row["학교명"],
                    "학년": row["학년"],
                    "매칭교재": roster_book,
                    "작성여부": "O" if count > 0 else "X",
                    "작성문제수": count,
                    "최근작성일시": answer["latest"],
                }
            )

    return pd.DataFrame(records)

def simplify_class_for_paper(class_name: str, grade: str, book_name: str) -> str:
    """
    PDF 상단 제목에 들어갈 짧은 수업명 생성.
    예: 화목토일(앞) 고2 미적분1 → 고2 미적분1
    """
    class_name = str(class_name or "").strip()
    grade = str(grade or "").strip()

    subject_map = {
        "미적분1 고쟁이": "미적분1",
        "확통 고쟁이": "확통",
        "미적분2 쎈": "미적분2",
        "기하 쎈": "기하",
        "공통수학2 고쟁이": "공통수학2",
        "공통수학2 RPM": "공통수학2",
        "마플교과서 공통수학1": "공통수학1",
        "공통수학1 RPM": "공통수학1",
    }

    subject = subject_map.get(book_name, "")
    if grade and subject:
        return f"{grade} {subject}"

    # 요일 및 앞/뒤 표기를 제거한 보조 처리
    cleaned = re.sub(r"^(월|화|수|목|금|토|일|,|\(|\)|앞|뒤)+\s*", "", class_name)
    return cleaned or class_name

def build_paper_title(
    teacher_name: str,
    class_name: str,
    grade: str,
    book_name: str,
    month: int,
    week: int
) -> str:
    teacher = str(teacher_name).replace(".", "").strip()
    course = simplify_class_for_paper(class_name, grade, book_name)
    return f"{teacher} {course} 오답 Paper - {month}월 {week}주차"

def build_claude_export_df(
    teacher_name: str,
    class_name: str,
    selected_students: list[str],
    selected_book: str,
    month: int,
    week: int,
) -> pd.DataFrame:
    roster = get_roster_df()
    answers = get_all_wrong_answers()

    selected_roster = roster[
        (roster["담당선생님"] == teacher_name)
        & (roster["반명"] == class_name)
        & (roster["학생명"].isin(selected_students))
    ].copy()

    records = []

    for _, student in selected_roster.iterrows():
        student_answers = answers[
            (answers["학생"] == student["학생명"])
            & (answers["교재"] == selected_book)
        ].copy()

        all_numbers = []
        all_memos = []

        for _, answer in student_answers.iterrows():
            for number in parse_problem_numbers(answer["문제번호"]):
                if number not in all_numbers:
                    all_numbers.append(number)

            memo = str(answer.get("비고", "") or "").strip()
            if memo and memo not in all_memos:
                all_memos.append(memo)

        title = build_paper_title(
            teacher_name,
            class_name,
            student["학년"],
            selected_book,
            month,
            week,
        )

        records.append(
            {
                "학생명": student["학생명"],
                "학교명": student["학교명"],
                "학년": student["학년"],
                "담당선생님": teacher_name,
                "반명": class_name,
                "교재": selected_book,
                "문제번호": format_problem_numbers(all_numbers),
                "비고": " / ".join(all_memos),
                "PDF상단제목": title,
                "파일명": (
                    f"[오답paper][{student['학년']} {student['학생명']}]"
                    f"[{month}월 {week}주차].pdf"
                ),
            }
        )

    return pd.DataFrame(records)

def create_password_reset_request(username: str) -> dict:
    username = str(username or "").strip()

    if not username:
        return {"ok": False, "message": "학생 이름을 입력해주세요."}

    user_response = (
        supabase.table("users")
        .select("username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    # 계정 존재 여부를 과하게 노출하지 않고 동일한 안내를 유지합니다.
    if not user_response.data:
        return {
            "ok": True,
            "message": (
                "비밀번호 재설정 요청을 확인했습니다. "
                "계정 정보가 확인되면 담당 선생님 또는 관리자가 처리합니다."
            ),
        }

    pending = (
        supabase.table("password_reset_requests")
        .select("id")
        .eq("username", username)
        .eq("status", "pending")
        .limit(1)
        .execute()
    )

    if pending.data:
        return {
            "ok": True,
            "message": "이미 처리 대기 중인 비밀번호 재설정 요청이 있습니다.",
        }

    supabase.table("password_reset_requests").insert(
        {
            "username": username,
            "status": "pending",
            "requested_at": now_kst_iso(),
            "processed_at": None,
            "processed_by": "",
        }
    ).execute()

    return {
        "ok": True,
        "message": (
            "비밀번호 재설정 요청이 접수되었습니다. "
            "담당 선생님 또는 관리자에게 임시 비밀번호를 확인해주세요."
        ),
    }

def get_password_reset_requests_df(
    teacher_name: str | None = None,
    pending_only: bool = False,
) -> pd.DataFrame:
    filters = [("status", "eq", "pending")] if pending_only else []

    rows = fetch_all_rows(
        "password_reset_requests",
        "id,username,status,requested_at,processed_at,processed_by",
        filters=filters,
        order_column="id",
        desc=True,
    )

    columns = [
        "요청ID", "학생", "상태", "요청일시", "처리일시", "처리자",
        "학교명", "학년", "반명", "담당선생님",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    roster = get_roster_df()
    roster_map: dict[str, dict] = {}

    if not roster.empty:
        for student_name, group in roster.groupby("학생명", sort=False):
            roster_map[str(student_name)] = {
                "학교명": ", ".join(
                    dict.fromkeys(
                        str(v).strip()
                        for v in group["학교명"]
                        if str(v).strip()
                    )
                ),
                "학년": ", ".join(
                    dict.fromkeys(
                        str(v).strip()
                        for v in group["학년"]
                        if str(v).strip()
                    )
                ),
                "반명": ", ".join(
                    dict.fromkeys(
                        str(v).strip()
                        for v in group["반명"]
                        if str(v).strip()
                    )
                ),
                "담당선생님": ", ".join(
                    dict.fromkeys(
                        normalize_teacher_name(v)
                        for v in group["담당선생님"]
                        if str(v).strip()
                    )
                ),
            }

    records = []

    for row in rows:
        username = str(row.get("username", "")).strip()
        info = roster_map.get(
            username,
            {"학교명": "", "학년": "", "반명": "", "담당선생님": ""},
        )

        records.append(
            {
                "요청ID": row.get("id"),
                "학생": username,
                "상태": row.get("status", ""),
                "요청일시": row.get("requested_at", ""),
                "처리일시": row.get("processed_at", ""),
                "처리자": row.get("processed_by", ""),
                **info,
            }
        )

    df = pd.DataFrame(records, columns=columns)

    if teacher_name and teacher_name != ALL_TEACHER_ADMIN:
        normalized_teacher = normalize_teacher_name(teacher_name)
        df = df[
            df["담당선생님"]
            .fillna("")
            .astype(str)
            .str.split(",")
            .apply(
                lambda values: normalized_teacher
                in [normalize_teacher_name(v.strip()) for v in values]
            )
        ].copy()

    return df.reset_index(drop=True)

def complete_password_reset_request(username: str, processed_by: str):
    pending_rows = fetch_all_rows(
        "password_reset_requests",
        "id",
        filters=[
            ("username", "eq", str(username).strip()),
            ("status", "eq", "pending"),
        ],
    )

    for row in pending_rows:
        (
            supabase.table("password_reset_requests")
            .update(
                {
                    "status": "completed",
                    "processed_at": now_kst_iso(),
                    "processed_by": str(processed_by or "").strip(),
                }
            )
            .eq("id", int(row["id"]))
            .execute()
        )

def is_temp_password_pending_change(username: str) -> bool:
    response = (
        supabase.table("users")
        .select("temp_password")
        .eq("username", str(username).strip())
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    return bool(str(response.data[0].get("temp_password") or "").strip())

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def find_signup_name_conflict(username: str) -> dict | None:
    """
    회원가입 이름이 기존 계정 또는 명단 학생 이름과 충돌하는지 확인합니다.

    예:
    - 명단 이름이 '양서율'인데 '양서율성신고'로 가입 시도
    - 기존 계정이 '양서율'인데 '양서율1'로 가입 시도
    위 경우 별도 계정 생성을 막고 관리자 문의를 안내합니다.
    """
    clean_name = re.sub(r"\s+", "", str(username or "").strip())

    if not clean_name:
        return None

    user_rows = fetch_all_rows("users", "username")
    roster_rows = fetch_all_rows("student_roster", "student_name,school_name")

    existing_user_names = sorted(
        {
            re.sub(r"\s+", "", str(row.get("username", "")).strip())
            for row in user_rows
            if str(row.get("username", "")).strip()
        },
        key=len,
        reverse=True,
    )

    roster_map: dict[str, str] = {}
    for row in roster_rows:
        roster_name = re.sub(
            r"\s+",
            "",
            str(row.get("student_name", "")).strip(),
        )
        if roster_name:
            roster_map.setdefault(
                roster_name,
                str(row.get("school_name", "")).strip(),
            )

    # 이미 정확히 같은 계정이 존재하는 경우
    if clean_name in existing_user_names:
        return {
            "type": "existing_account",
            "matched_name": clean_name,
            "school_name": roster_map.get(clean_name, ""),
        }

    # 명단에 정확히 존재하는 이름이고 아직 계정이 없다면 정상 가입 허용
    if clean_name in roster_map:
        return None

    candidate_names = sorted(
        set(existing_user_names) | set(roster_map.keys()),
        key=len,
        reverse=True,
    )

    # 본인 이름 뒤에 학교명·숫자 등을 붙인 별도 계정 생성을 차단
    for candidate in candidate_names:
        if len(candidate) < 2:
            continue

        if candidate in clean_name or clean_name in candidate:
            return {
                "type": "similar_name",
                "matched_name": candidate,
                "school_name": roster_map.get(candidate, ""),
            }

    return None

def create_user(username: str, password: str, grade: str) -> bool:
    username = username.strip()

    if not username:
        return False

    existing = (
        supabase.table("users")
        .select("username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if existing.data:
        return False

    supabase.table("users").insert(
        {
            "username": username,
            "password_hash": hash_pw(password),
            "grade": grade,
            "temp_password": "",
            "created_at": now_kst_iso()
        }
    ).execute()

    return True

def check_user(username: str, password: str) -> bool:
    response = (
        supabase.table("users")
        .select("password_hash")
        .eq("username", username.strip())
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    return response.data[0]["password_hash"] == hash_pw(password)

def change_my_password(
    username: str,
    current_password: str,
    new_password: str
) -> bool:
    """학생 본인이 현재 비밀번호를 확인한 뒤 새 비밀번호로 변경합니다."""
    if not check_user(username, current_password):
        return False

    supabase.table("users").update(
        {
            "password_hash": hash_pw(new_password),
            "temp_password": ""
        }
    ).eq("username", username).execute()

    return True

def get_admin_password_status() -> pd.DataFrame:
    """
    관리자는 복구·초기화 때 설정한 임시 비밀번호만 확인합니다.
    학생이 직접 변경한 비밀번호는 해시만 저장되므로 확인할 수 없습니다.
    """
    rows = fetch_all_rows(
        "users",
        "username,grade,temp_password,created_at",
        order_column="created_at",
        desc=True
    )

    if not rows:
        return pd.DataFrame(
            columns=["학생", "학년", "비밀번호상태", "가입일시"]
        )

    records = []

    for row in rows:
        temp_password = row.get("temp_password") or ""
        records.append(
            {
                "학생": row.get("username", ""),
                "학년": row.get("grade") or "미지정",
                "비밀번호상태": (
                    temp_password
                    if temp_password
                    else "학생이 직접 변경함"
                ),
                "가입일시": row.get("created_at", "")
            }
        )

    return pd.DataFrame(records)

def parse_problem_numbers(value: str) -> list[str]:
    """
    쉼표, 띄어쓰기, 줄바꿈이 섞여 있어도 숫자만 순서대로 추출합니다.
    예: '371, 499, 486, 587 961' → ['371', '499', '486', '587', '961']
    """
    numbers = re.findall(r"\d+", str(value or ""))
    return list(dict.fromkeys(numbers))

def format_problem_numbers(numbers: list[str]) -> str:
    return ", ".join(numbers)

def get_existing_problem_numbers(username: str, book: str) -> set[str]:
    rows = fetch_all_rows(
        "wrong_answers",
        "problem",
        filters=[
            ("username", "eq", username),
            ("unit", "eq", book),
        ],
    )

    existing: set[str] = set()

    for row in rows:
        existing.update(parse_problem_numbers(row.get("problem", "")))

    return existing

def add_wrong_answer(
    username: str,
    book: str,
    problem_number: str,
    note: str
) -> dict:
    submitted_numbers = parse_problem_numbers(problem_number)

    if not submitted_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": [],
            "message": "저장할 문제번호가 없습니다.",
        }

    existing_numbers = get_existing_problem_numbers(username, book)

    new_numbers = [
        number
        for number in submitted_numbers
        if number not in existing_numbers
    ]
    duplicate_numbers = [
        number
        for number in submitted_numbers
        if number in existing_numbers
    ]

    if not new_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": duplicate_numbers,
            "message": "입력한 문제번호가 모두 이미 저장되어 있습니다.",
        }

    supabase.table("wrong_answers").insert(
        {
            "username": username,
            "unit": book,
            "problem": format_problem_numbers(new_numbers),
            "memo": note,
            "created_at": now_kst_iso(),
        }
    ).execute()

    return {
        "saved": True,
        "new_numbers": new_numbers,
        "duplicate_numbers": duplicate_numbers,
        "message": "새 문제번호만 저장했습니다.",
    }

def cleanup_duplicate_wrong_answers() -> dict:
    """
    학생·교재별 작성 순서대로 확인하여 이미 저장된 번호는 뒤 기록에서 제거합니다.
    완전히 같은 중복 행은 삭제합니다.
    """
    rows = fetch_all_rows(
        "wrong_answers",
        "id,username,unit,problem,created_at",
        order_column="id",
        desc=False,
    )

    seen_by_group: dict[tuple[str, str], set[str]] = {}
    updated_count = 0
    deleted_count = 0

    for row in rows:
        row_id = row.get("id")
        username = str(row.get("username", ""))
        unit = str(row.get("unit", ""))
        group_key = (username, unit)

        seen = seen_by_group.setdefault(group_key, set())
        numbers = parse_problem_numbers(row.get("problem", ""))

        new_numbers = [number for number in numbers if number not in seen]

        if not new_numbers:
            (
                supabase.table("wrong_answers")
                .delete()
                .eq("id", row_id)
                .execute()
            )
            deleted_count += 1
            continue

        normalized_problem = format_problem_numbers(new_numbers)
        original_problem = str(row.get("problem", "")).strip()

        if normalized_problem != original_problem:
            (
                supabase.table("wrong_answers")
                .update({"problem": normalized_problem})
                .eq("id", row_id)
                .execute()
            )
            updated_count += 1

        seen.update(new_numbers)

    return {
        "updated": updated_count,
        "deleted": deleted_count,
    }

def get_my_wrong_answers(username: str) -> pd.DataFrame:
    rows = fetch_all_rows(
        "wrong_answers",
        "unit,problem,memo,created_at,id",
        filters=[("username", "eq", username)],
        order_column="id",
        desc=True
    )

    if not rows:
        return pd.DataFrame(
            columns=["교재", "문제번호", "비고", "작성일시"]
        )

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "unit": "교재",
            "problem": "문제번호",
            "memo": "비고",
            "created_at": "작성일시"
        }
    )

    return df[["교재", "문제번호", "비고", "작성일시"]]

def get_wrong_answer_edit_records() -> pd.DataFrame:
    rows = fetch_all_rows(
        "wrong_answers",
        "id,username,unit,problem,memo,created_at",
        order_column="id",
        desc=True,
    )

    if not rows:
        return pd.DataFrame(
            columns=["기록ID", "학생", "교재", "문제번호", "비고", "작성일시"]
        )

    return pd.DataFrame(
        [
            {
                "기록ID": row.get("id"),
                "학생": row.get("username", ""),
                "교재": row.get("unit", ""),
                "문제번호": row.get("problem", ""),
                "비고": row.get("memo", ""),
                "작성일시": row.get("created_at", ""),
            }
            for row in rows
        ]
    )

def update_wrong_answer_book(record_id: int, new_book: str):
    (
        supabase.table("wrong_answers")
        .update({"unit": new_book})
        .eq("id", int(record_id))
        .execute()
    )
    cleanup_duplicate_wrong_answers()

def update_wrong_answer_xpattern_school(
    record_id: int,
    original_numbers: list,
    new_school: str,
    new_block: dict,
):
    """
    학생이 X-패턴 교재에서 학교를 잘못 선택해 엉뚱한 내부번호로 저장된 기록을,
    관리자가 올바른 학교(+시험)를 다시 골라 원래 시험지 번호 기준으로 재변환합니다.
    """
    offset = new_block["offset"]
    converted = [str(offset + int(n)) for n in original_numbers]
    new_problem = ", ".join(converted)

    exam_tag = new_block["exam_type"]
    new_memo_prefix = f"[{new_school}" + (f" {exam_tag}" if exam_tag else "") + "] "

    current = (
        supabase.table("wrong_answers")
        .select("memo")
        .eq("id", int(record_id))
        .limit(1)
        .execute()
    )
    old_memo = str(current.data[0].get("memo", "") or "") if current.data else ""
    # 기존 "[학교 시험]" 형태 태그가 있으면 새 태그로 교체하고, 없으면 뒤에 이어 붙인다.
    stripped_memo = re.sub(r"^\[[^\]]*\]\s*", "", old_memo).strip()
    new_memo = (new_memo_prefix + stripped_memo).strip()

    (
        supabase.table("wrong_answers")
        .update({"problem": new_problem, "memo": new_memo})
        .eq("id", int(record_id))
        .execute()
    )
    cleanup_duplicate_wrong_answers()

def get_all_wrong_answers() -> pd.DataFrame:
    answer_rows = fetch_all_rows(
        "wrong_answers",
        "id,username,unit,problem,memo,created_at",
        order_column="id",
        desc=True
    )

    if not answer_rows:
        return pd.DataFrame(
            columns=["학생", "학년", "교재", "문제번호", "비고", "작성일시"]
        )

    user_rows = fetch_all_rows("users", "username,grade")
    grade_map = {
        row.get("username", ""): row.get("grade") or "미지정"
        for row in user_rows
    }

    records = []

    for row in answer_rows:
        username = row.get("username", "")
        records.append(
            {
                "학생": username,
                "학년": grade_map.get(username, "미지정"),
                "교재": row.get("unit", ""),
                "문제번호": row.get("problem", ""),
                "비고": row.get("memo", ""),
                "작성일시": row.get("created_at", "")
            }
        )

    return pd.DataFrame(records)

def merge_wrong_answers_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    같은 학생이 같은 날짜에 같은 교재로 여러 번 입력한 오답 기록을 한 줄로 합칩니다.
    문제번호는 중복 없이 입력 순서대로 합치고, 비고도 중복 문구를 제거해 합칩니다.
    """
    output_columns = ["학생", "학년", "교재", "문제번호", "비고", "작성일시"]

    if df.empty:
        return pd.DataFrame(columns=output_columns)

    working = df.copy()
    working["작성일시"] = working["작성일시"].fillna("").astype(str)
    working["작성날짜"] = working["작성일시"].str.slice(0, 10)

    # 날짜 형식이 없는 예외 데이터는 기존 작성일시를 사용합니다.
    working.loc[
        working["작성날짜"].str.len() != 10,
        "작성날짜"
    ] = working["작성일시"]

    merged_records = []

    grouped = working.groupby(
        ["학생", "학년", "교재", "작성날짜"],
        sort=False,
        dropna=False,
    )

    for (student, grade, book, created_date), group in grouped:
        merged_numbers = []
        merged_memos = []

        for _, row in group.iterrows():
            for number in parse_problem_numbers(row.get("문제번호", "")):
                if number not in merged_numbers:
                    merged_numbers.append(number)

            memo = str(row.get("비고", "") or "").strip()
            if memo and memo.lower() != "nan" and memo not in merged_memos:
                merged_memos.append(memo)

        merged_records.append(
            {
                "학생": student,
                "학년": grade,
                "교재": book,
                "문제번호": format_problem_numbers(merged_numbers),
                "비고": " / ".join(merged_memos),
                "작성일시": created_date,
            }
        )

    return pd.DataFrame(merged_records, columns=output_columns)

def get_print_status_rows(
    teacher_name: str | None = None
) -> pd.DataFrame:
    """출력 관리 상태를 조회합니다."""
    filters = []

    if teacher_name and teacher_name != ALL_TEACHER_ADMIN:
        filters.append(("teacher_name", "eq", teacher_name))

    rows = fetch_all_rows(
        "print_status",
        (
            "id,teacher_name,class_name,student_name,book_name,"
            "month,week,is_printed,printed_at,memo,created_at"
        ),
        filters=filters,
        order_column="id",
        desc=True,
    )

    columns = [
        "기록ID", "담당선생님", "반명", "학생명", "교재",
        "월", "주차", "출력완료", "출력일시", "메모", "등록일시"
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "기록ID": row.get("id"),
                "담당선생님": row.get("teacher_name", ""),
                "반명": row.get("class_name", ""),
                "학생명": row.get("student_name", ""),
                "교재": row.get("book_name", ""),
                "월": row.get("month"),
                "주차": row.get("week"),
                "출력완료": bool(row.get("is_printed", False)),
                "출력일시": row.get("printed_at", ""),
                "메모": row.get("memo", ""),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )

def ensure_print_status_records(
    teacher_name: str,
    class_name: str,
    month: int,
    week: int,
):
    """
    선택한 선생님·반·월·주차의 학생들을 출력 관리 목록에 생성합니다.
    이미 존재하는 학생은 중복 생성하지 않습니다.
    """
    roster = get_roster_df()

    target = roster[
        (roster["담당선생님"] == teacher_name)
        & (roster["반명"] == class_name)
    ].copy()

    if target.empty:
        return 0

    existing_rows = fetch_all_rows(
        "print_status",
        "student_name,book_name",
        filters=[
            ("teacher_name", "eq", teacher_name),
            ("class_name", "eq", class_name),
            ("month", "eq", int(month)),
            ("week", "eq", int(week)),
        ],
    )

    existing_keys = {
        (
            str(row.get("student_name", "")).strip(),
            str(row.get("book_name", "")).strip(),
        )
        for row in existing_rows
    }

    insert_rows = []

    for _, row in target.iterrows():
        key = (
            str(row["학생명"]).strip(),
            str(row["매칭교재"]).strip(),
        )

        if key in existing_keys:
            continue

        insert_rows.append(
            {
                "teacher_name": teacher_name,
                "class_name": class_name,
                "student_name": row["학생명"],
                "book_name": row["매칭교재"],
                "month": int(month),
                "week": int(week),
                "is_printed": False,
                "printed_at": None,
                "memo": "",
                "created_at": now_kst_iso(),
            }
        )

    if insert_rows:
        supabase.table("print_status").insert(insert_rows).execute()

    return len(insert_rows)

def ensure_selected_print_status_records(
    teacher_name: str,
    class_name: str,
    student_names: list[str],
    book_name: str,
    month: int,
    week: int,
) -> int:
    """
    오답노트 생성 대상으로 선택된 학생만 출력 관리 목록에 등록합니다.
    이미 등록된 학생·교재·월·주차 조합은 중복 생성하지 않습니다.
    """
    clean_students = [
        str(name).strip()
        for name in student_names
        if str(name).strip()
    ]

    if not clean_students:
        return 0

    roster = get_roster_df()

    target = roster[
        (roster["담당선생님"] == teacher_name)
        & (roster["반명"] == class_name)
        & (roster["학생명"].isin(clean_students))
    ].copy()

    if target.empty:
        return 0

    existing_rows = fetch_all_rows(
        "print_status",
        "student_name,book_name",
        filters=[
            ("teacher_name", "eq", teacher_name),
            ("class_name", "eq", class_name),
            ("month", "eq", int(month)),
            ("week", "eq", int(week)),
        ],
    )

    existing_keys = {
        (
            str(row.get("student_name", "")).strip(),
            str(row.get("book_name", "")).strip(),
        )
        for row in existing_rows
    }

    insert_rows = []

    for _, row in target.iterrows():
        student_name = str(row["학생명"]).strip()
        selected_book_name = str(book_name).strip()
        key = (student_name, selected_book_name)

        if key in existing_keys:
            continue

        insert_rows.append(
            {
                "teacher_name": teacher_name,
                "class_name": class_name,
                "student_name": student_name,
                "book_name": selected_book_name,
                "month": int(month),
                "week": int(week),
                "is_printed": False,
                "printed_at": None,
                "memo": "",
                "created_at": now_kst_iso(),
            }
        )

    if insert_rows:
        supabase.table("print_status").insert(insert_rows).execute()

    return len(insert_rows)

def register_print_queue_on_download(
    teacher_name: str,
    class_name: str,
    student_names: list[str],
    book_name: str,
    month: int,
    week: int,
):
    """
    Claude Code용 오답노트 엑셀 다운로드 버튼을 누를 때
    선택 학생을 출력 대기 목록에 자동 등록합니다.
    """
    try:
        created_count = ensure_selected_print_status_records(
            teacher_name,
            class_name,
            student_names,
            book_name,
            month,
            week,
        )
        st.session_state["print_auto_register_result"] = {
            "created_count": created_count,
            "student_count": len(student_names),
            "teacher_name": teacher_name,
            "class_name": class_name,
            "month": month,
            "week": week,
        }
    except Exception as error:
        st.session_state["print_auto_register_error"] = str(error)

def update_print_status_bulk(
    record_ids: list[int],
    is_printed: bool,
) -> int:
    """여러 출력 관리 기록을 한 번에 완료 또는 미완료로 변경합니다."""
    clean_ids = sorted(
        {
            int(record_id)
            for record_id in record_ids
            if record_id is not None
        }
    )

    if not clean_ids:
        return 0

    payload = {
        "is_printed": bool(is_printed),
        "printed_at": now_kst_iso() if is_printed else None,
    }

    updated_count = 0

    # Supabase Python 클라이언트 버전 차이를 피하기 위해
    # 한 건씩 안정적으로 업데이트합니다.
    for record_id in clean_ids:
        response = (
            supabase.table("print_status")
            .update(payload)
            .eq("id", record_id)
            .execute()
        )
        updated_count += len(response.data or [])

    return updated_count

def update_print_status(
    record_id: int,
    *,
    is_printed: bool,
    memo: str,
):
    """출력 완료 여부와 메모를 저장합니다."""
    payload = {
        "is_printed": bool(is_printed),
        "memo": str(memo or "").strip(),
        "printed_at": now_kst_iso() if is_printed else None,
    }

    (
        supabase.table("print_status")
        .update(payload)
        .eq("id", int(record_id))
        .execute()
    )

def delete_print_status_record(record_id: int):
    (
        supabase.table("print_status")
        .delete()
        .eq("id", int(record_id))
        .execute()
    )

def get_monday(date_value: datetime | None = None) -> datetime:
    """입력 날짜가 포함된 주의 월요일 00:00을 반환합니다."""
    current = date_value or datetime.now(KST).replace(tzinfo=None)
    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
    return current - timedelta(days=current.weekday())

def build_week_options(weeks_back: int = 12) -> dict[str, datetime]:
    """이번 주부터 과거 주차까지 선택 가능한 목록을 생성합니다."""
    current_monday = get_monday()
    options: dict[str, datetime] = {}

    for offset in range(weeks_back):
        week_start = current_monday - timedelta(weeks=offset)
        week_end = week_start + timedelta(days=6)
        month_week = ((week_start.day - 1) // 7) + 1

        prefix = "이번 주 · " if offset == 0 else ""
        label = (
            f"{prefix}{week_start.month}월 {month_week}주차 "
            f"({week_start.month}/{week_start.day} 월 ~ "
            f"{week_end.month}/{week_end.day} 일)"
        )
        options[label] = week_start

    return options

def parse_created_at_to_datetime(value) -> datetime | None:
    """Supabase 작성일시 문자열을 비교 가능한 datetime으로 변환합니다."""
    raw = str(value or "").strip()

    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(KST).replace(tzinfo=None)

        return parsed
    except Exception:
        return None

def get_weekly_submission_df(
    current_teacher: str,
    week_start: datetime,
) -> pd.DataFrame:
    """
    명단 학생을 기준으로 해당 주 월요일~일요일의 제출 여부를 계산합니다.
    해당 기간에 문제번호를 1개 이상 저장하면 제출로 처리합니다.
    """
    roster = get_roster_df()

    output_columns = [
        "담당선생님", "반명", "학생명", "학교명", "학년",
        "제출여부", "제출문제수", "제출교재", "최근제출일시",
    ]

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    if current_teacher != ALL_TEACHER_ADMIN:
        roster = roster[
            roster["담당선생님"] == current_teacher
        ].copy()

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    # 같은 학생이 같은 반에서 여러 교재로 명단에 등록된 경우 한 명으로 통합합니다.
    roster_students = (
        roster[
            ["담당선생님", "반명", "학생명", "학교명", "학년"]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    answer_rows = fetch_all_rows(
        "wrong_answers",
        "username,unit,problem,created_at",
        order_column="id",
        desc=False,
    )

    week_end_exclusive = week_start + timedelta(days=7)
    submission_map: dict[str, dict] = {}

    for row in answer_rows:
        created_dt = parse_created_at_to_datetime(row.get("created_at"))

        if created_dt is None:
            continue

        if not (week_start <= created_dt < week_end_exclusive):
            continue

        username = str(row.get("username", "")).strip()
        if not username:
            continue

        info = submission_map.setdefault(
            username,
            {
                "numbers": [],
                "books": [],
                "latest_dt": None,
                "latest_text": "",
            },
        )

        for number in parse_problem_numbers(row.get("problem", "")):
            if number not in info["numbers"]:
                info["numbers"].append(number)

        book = str(row.get("unit", "")).strip()
        if book and book not in info["books"]:
            info["books"].append(book)

        if info["latest_dt"] is None or created_dt > info["latest_dt"]:
            info["latest_dt"] = created_dt
            info["latest_text"] = created_dt.strftime("%Y.%m.%d %H:%M")

    records = []

    for _, student in roster_students.iterrows():
        student_name = str(student["학생명"]).strip()
        submission = submission_map.get(
            student_name,
            {
                "numbers": [],
                "books": [],
                "latest_text": "",
            },
        )
        problem_count = len(submission["numbers"])

        records.append(
            {
                "담당선생님": student["담당선생님"],
                "반명": student["반명"],
                "학생명": student_name,
                "학교명": student["학교명"],
                "학년": student["학년"],
                "제출여부": "O" if problem_count > 0 else "X",
                "제출문제수": problem_count,
                "제출교재": ", ".join(submission["books"]),
                "최근제출일시": submission["latest_text"],
            }
        )

    return pd.DataFrame(records, columns=output_columns)

def get_student_signup_status_df(
    current_teacher: str,
) -> pd.DataFrame:
    """
    학생 명단과 실제 users 계정을 비교하여 가입 상태를 계산합니다.

    상태:
    - 가입 완료: 명단 학생명과 계정명이 정확히 일치
    - 유사 계정 있음: 이름 뒤에 학교명·숫자 등이 붙은 유사 계정 존재
    - 미가입: 정확하거나 유사한 계정이 없음
    """
    roster = get_roster_df()

    output_columns = [
        "담당선생님",
        "학생명",
        "학교명",
        "학년",
        "소속반",
        "가입상태",
        "계정명",
        "가입일시",
        "오답개수",
    ]

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    if current_teacher != ALL_TEACHER_ADMIN:
        normalized_current_teacher = normalize_teacher_name(
            current_teacher
        )
        roster = roster[
            roster["담당선생님"].apply(normalize_teacher_name)
            == normalized_current_teacher
        ].copy()

    if roster.empty:
        return pd.DataFrame(columns=output_columns)

    users_df = get_all_users()

    if users_df.empty:
        users_df = pd.DataFrame(
            columns=["학생", "학년", "가입일시", "오답개수"]
        )

    account_map = {
        str(row["학생"]).strip(): {
            "가입일시": row.get("가입일시", ""),
            "오답개수": int(row.get("오답개수", 0) or 0),
        }
        for _, row in users_df.iterrows()
        if str(row.get("학생", "")).strip()
    }

    account_names = sorted(
        account_map.keys(),
        key=lambda value: (len(value), value),
    )

    grouped_roster = (
        roster.groupby(
            [
                "담당선생님",
                "학생명",
                "학교명",
                "학년",
            ],
            dropna=False,
            sort=False,
        )["반명"]
        .apply(
            lambda values: ", ".join(
                dict.fromkeys(
                    str(value).strip()
                    for value in values
                    if str(value).strip()
                )
            )
        )
        .reset_index(name="소속반")
    )

    records = []

    for _, student in grouped_roster.iterrows():
        student_name = str(student["학생명"]).strip()
        compact_student_name = re.sub(r"\\s+", "", student_name)

        exact_account = (
            student_name
            if student_name in account_map
            else None
        )

        similar_accounts = []

        if exact_account is None:
            for account_name in account_names:
                compact_account_name = re.sub(
                    r"\\s+",
                    "",
                    account_name,
                )

                if not compact_account_name:
                    continue

                if (
                    compact_account_name.startswith(
                        compact_student_name
                    )
                    or compact_student_name.startswith(
                        compact_account_name
                    )
                ):
                    similar_accounts.append(account_name)

        if exact_account:
            signup_status = "가입 완료"
            account_display = exact_account
            joined_at = account_map[exact_account]["가입일시"]
            answer_count = account_map[exact_account]["오답개수"]
        elif similar_accounts:
            signup_status = "유사 계정 있음"
            account_display = ", ".join(similar_accounts)
            joined_at = ", ".join(
                str(account_map[name]["가입일시"])
                for name in similar_accounts
                if str(account_map[name]["가입일시"]).strip()
            )
            answer_count = sum(
                int(account_map[name]["오답개수"])
                for name in similar_accounts
            )
        else:
            signup_status = "미가입"
            account_display = ""
            joined_at = ""
            answer_count = 0

        records.append(
            {
                "담당선생님": normalize_teacher_name(
                    student["담당선생님"]
                ),
                "학생명": student_name,
                "학교명": student["학교명"],
                "학년": student["학년"],
                "소속반": student["소속반"],
                "가입상태": signup_status,
                "계정명": account_display,
                "가입일시": joined_at,
                "오답개수": answer_count,
            }
        )

    return pd.DataFrame(records, columns=output_columns)

def parse_book_bulk_text(raw_text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows = []
    error_rows = []

    lines = [
        line.strip()
        for line in str(raw_text or "").splitlines()
        if line.strip()
    ]

    for line_number, line in enumerate(lines, start=1):
        try:
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
            elif "\t" in line:
                parts = [part.strip() for part in line.split("\t")]
            else:
                parts = [line]

            parts += [""] * (6 - len(parts))
            book_name, grade, subject, publisher, count_raw, category = parts[:6]

            book_name = str(book_name).strip()
            category = str(category).strip() or "교재"

            if not book_name:
                raise ValueError("교재명이 비어 있습니다.")

            if str(count_raw).strip():
                digits = re.sub(r"[^0-9]", "", str(count_raw))
                if not digits:
                    raise ValueError("문항 수를 숫자로 입력해주세요.")
                question_count = int(digits)
            else:
                question_count = None

            valid_rows.append(
                {
                    "줄번호": line_number,
                    "교재명": book_name,
                    "학년": str(grade).strip(),
                    "과목": str(subject).strip(),
                    "출판사": str(publisher).strip(),
                    "문항수": question_count,
                    "분류": category,
                    "원문": line,
                }
            )
        except Exception as error:
            error_rows.append(
                {
                    "줄번호": line_number,
                    "원문": line,
                    "오류": str(error),
                }
            )

    return (
        pd.DataFrame(valid_rows),
        pd.DataFrame(error_rows),
    )

def register_book_rows(valid_df: pd.DataFrame) -> dict:
    if valid_df.empty:
        return {"created": 0, "skipped": 0}

    existing_df = get_book_master_df(active_only=False)
    existing_names = set(
        existing_df.get("교재명", pd.Series(dtype=str))
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    rows = []
    skipped = 0

    for _, row in valid_df.iterrows():
        book_name = str(row["교재명"]).strip()

        if book_name in existing_names:
            skipped += 1
            continue

        rows.append(
            {
                "book_name": book_name,
                "grade": str(row.get("학년", "") or "").strip(),
                "subject": str(row.get("과목", "") or "").strip(),
                "publisher": str(row.get("출판사", "") or "").strip(),
                "question_count": (
                    int(row["문항수"])
                    if pd.notna(row.get("문항수"))
                    else None
                ),
                "category": str(row.get("분류", "교재") or "교재").strip(),
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )
        existing_names.add(book_name)

    if rows:
        supabase.table("book_master").insert(rows).execute()

    return {"created": len(rows), "skipped": skipped}

def set_book_active(book_id: int, is_active: bool):
    (
        supabase.table("book_master")
        .update({"is_active": bool(is_active)})
        .eq("id", int(book_id))
        .execute()
    )

def update_book_master(
    book_id: int,
    book_name: str,
    grade: str,
    subject: str,
    publisher: str,
    question_count: int | None,
    category: str,
):
    current = (
        supabase.table("book_master")
        .select("book_name")
        .eq("id", int(book_id))
        .limit(1)
        .execute()
    )

    if not current.data:
        raise ValueError("수정할 교재를 찾을 수 없습니다.")

    old_name = str(current.data[0].get("book_name", "")).strip()
    new_name = str(book_name or "").strip()

    if not new_name:
        raise ValueError("교재명을 입력해주세요.")

    (
        supabase.table("book_master")
        .update(
            {
                "book_name": new_name,
                "grade": str(grade or "").strip(),
                "subject": str(subject or "").strip(),
                "publisher": str(publisher or "").strip(),
                "question_count": question_count,
                "category": str(category or "교재").strip(),
            }
        )
        .eq("id", int(book_id))
        .execute()
    )

    if old_name and old_name != new_name:
        supabase.table("wrong_answers").update(
            {"unit": new_name}
        ).eq("unit", old_name).execute()

        supabase.table("print_status").update(
            {"book_name": new_name}
        ).eq("book_name", old_name).execute()

def initialize_default_books() -> int:
    existing_df = get_book_master_df(active_only=False)
    existing_names = set(
        existing_df.get("교재명", pd.Series(dtype=str))
        .dropna()
        .astype(str)
        .tolist()
    )

    rows = []

    for name in BOOKS:
        if name in existing_names:
            continue

        rows.append(
            {
                "book_name": name,
                "grade": "",
                "subject": "",
                "publisher": "",
                "question_count": None,
                "category": "기존 교재",
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )

    if rows:
        supabase.table("book_master").insert(rows).execute()

    return len(rows)

def make_school_exam_display_name(
    exam_year: int,
    school_name: str,
    subject: str,
    exam_type: str,
) -> str:
    parts = [
        str(exam_year).strip(),
        str(subject or "").strip(),
        str(school_name or "").strip(),
        str(exam_type or "").strip(),
    ]
    return " ".join(part for part in parts if part)

def normalize_exam_year(value) -> int:
    raw = re.sub(r"[^0-9]", "", str(value or ""))

    if not raw:
        raise ValueError("연도를 확인할 수 없습니다.")

    year = int(raw)

    if year < 100:
        year += 2000

    if year < 2000 or year > 2100:
        raise ValueError("연도는 2000~2100 사이로 입력해주세요.")

    return year

def parse_school_exam_bulk_text(raw_text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    관리자 메모장 복붙 내용을 학교 기출 목록으로 변환합니다.

    권장 형식:
    연도 | 학교 | 과목 | 시험구분 | 문항수 | 범위

    예:
    2025 | 울산고 | 미적분1 | 2학기 중간 | 30 | 함수의 극한~접선
    2025 | 학성고 | 미적분1 | 2학기 중간 | 28 |

    탭 또는 쉼표 구분도 허용합니다.
    간단 형식 '2025 미적분1 울산고 시험'도 인식하지만,
    정확한 등록을 위해 구분자 형식을 권장합니다.
    """
    valid_rows = []
    error_rows = []

    lines = [
        line.strip()
        for line in str(raw_text or "").splitlines()
        if line.strip()
    ]

    for line_number, line in enumerate(lines, start=1):
        try:
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
            elif "\t" in line:
                parts = [part.strip() for part in line.split("\t")]
            elif "," in line and line.count(",") >= 3:
                parts = [part.strip() for part in line.split(",")]
            else:
                # 간단 문장형 보조 인식
                tokens = line.split()
                if len(tokens) < 4:
                    raise ValueError(
                        "항목이 부족합니다. 연도 | 학교 | 과목 | 시험구분 형식으로 입력해주세요."
                    )

                year_token = tokens[0]
                school_index = next(
                    (
                        index
                        for index, token in enumerate(tokens[1:], start=1)
                        if token.endswith(("고", "여고", "외고", "중"))
                    ),
                    None,
                )

                if school_index is None:
                    raise ValueError("학교명을 확인할 수 없습니다.")

                subject = tokens[1] if school_index != 1 else (
                    tokens[2] if len(tokens) > 2 else ""
                )
                school_name = tokens[school_index]
                exam_tokens = [
                    token
                    for index, token in enumerate(tokens[1:], start=1)
                    if index not in {school_index}
                    and token != subject
                ]

                parts = [
                    year_token,
                    school_name,
                    subject,
                    " ".join(exam_tokens) or "시험",
                    "",
                    "",
                ]

            parts += [""] * (6 - len(parts))
            year_raw, school_name, subject, exam_type, question_count_raw, scope = parts[:6]

            exam_year = normalize_exam_year(year_raw)
            school_name = str(school_name).strip()
            subject = str(subject).strip()
            exam_type = str(exam_type).strip() or "시험"
            scope = str(scope).strip()

            if not school_name:
                raise ValueError("학교가 비어 있습니다.")
            if not subject:
                raise ValueError("과목이 비어 있습니다.")

            if str(question_count_raw).strip():
                question_count = int(
                    re.sub(r"[^0-9]", "", str(question_count_raw))
                )
                if question_count <= 0:
                    raise ValueError("문항 수는 1 이상이어야 합니다.")
            else:
                question_count = None

            display_name = make_school_exam_display_name(
                exam_year,
                school_name,
                subject,
                exam_type,
            )

            valid_rows.append(
                {
                    "줄번호": line_number,
                    "연도": exam_year,
                    "학교": school_name,
                    "과목": subject,
                    "시험구분": exam_type,
                    "문항수": question_count,
                    "범위": scope,
                    "표시명": display_name,
                    "원문": line,
                }
            )
        except Exception as error:
            error_rows.append(
                {
                    "줄번호": line_number,
                    "원문": line,
                    "오류": str(error),
                }
            )

    valid_df = pd.DataFrame(
        valid_rows,
        columns=[
            "줄번호", "연도", "학교", "과목", "시험구분",
            "문항수", "범위", "표시명", "원문",
        ],
    )
    error_df = pd.DataFrame(
        error_rows,
        columns=["줄번호", "원문", "오류"],
    )

    return valid_df, error_df

def get_school_exam_master_df(active_only: bool = True) -> pd.DataFrame:
    filters = [("is_active", "eq", True)] if active_only else []

    rows = fetch_all_rows(
        "school_exam_master",
        (
            "id,exam_year,school_name,subject,exam_type,"
            "question_count,scope,display_name,is_active,created_at"
        ),
        filters=filters,
        order_column="exam_year",
        desc=True,
    )

    columns = [
        "기출ID", "연도", "학교", "과목", "시험구분",
        "문항수", "범위", "표시명", "사용중", "등록일시",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "기출ID": row.get("id"),
                "연도": row.get("exam_year"),
                "학교": row.get("school_name", ""),
                "과목": row.get("subject", ""),
                "시험구분": row.get("exam_type", ""),
                "문항수": row.get("question_count"),
                "범위": row.get("scope", ""),
                "표시명": row.get("display_name", ""),
                "사용중": bool(row.get("is_active", True)),
                "등록일시": row.get("created_at", ""),
            }
            for row in rows
        ],
        columns=columns,
    )

def register_school_exam_rows(valid_df: pd.DataFrame) -> dict:
    if valid_df.empty:
        return {"created": 0, "skipped": 0}

    existing_df = get_school_exam_master_df(active_only=False)
    existing_keys = {
        (
            int(row["연도"]),
            str(row["학교"]).strip(),
            str(row["과목"]).strip(),
            str(row["시험구분"]).strip(),
        )
        for _, row in existing_df.iterrows()
    }

    insert_rows = []
    skipped = 0

    for _, row in valid_df.iterrows():
        key = (
            int(row["연도"]),
            str(row["학교"]).strip(),
            str(row["과목"]).strip(),
            str(row["시험구분"]).strip(),
        )

        if key in existing_keys:
            skipped += 1
            continue

        insert_rows.append(
            {
                "exam_year": int(row["연도"]),
                "school_name": str(row["학교"]).strip(),
                "subject": str(row["과목"]).strip(),
                "exam_type": str(row["시험구분"]).strip(),
                "question_count": (
                    int(row["문항수"])
                    if pd.notna(row["문항수"])
                    else None
                ),
                "scope": str(row["범위"] or "").strip(),
                "display_name": str(row["표시명"]).strip(),
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )
        existing_keys.add(key)

    if insert_rows:
        supabase.table("school_exam_master").insert(insert_rows).execute()

    return {
        "created": len(insert_rows),
        "skipped": skipped,
    }

def set_school_exam_active(exam_id: int, is_active: bool):
    (
        supabase.table("school_exam_master")
        .update({"is_active": bool(is_active)})
        .eq("id", int(exam_id))
        .execute()
    )

def get_existing_school_exam_numbers(
    username: str,
    exam_id: int,
) -> set[str]:
    rows = fetch_all_rows(
        "school_exam_wrong_answers",
        "problem",
        filters=[
            ("username", "eq", username),
            ("exam_id", "eq", int(exam_id)),
        ],
    )

    numbers = set()

    for row in rows:
        numbers.update(parse_problem_numbers(row.get("problem", "")))

    return numbers

def add_school_exam_wrong_answer(
    username: str,
    exam_id: int,
    problem_number: str,
    memo: str,
    source_type: str = "manual",
    source_filename: str = "",
) -> dict:
    submitted_numbers = parse_problem_numbers(problem_number)

    if not submitted_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": [],
            "message": "저장할 기출 오답번호가 없습니다.",
        }

    existing_numbers = get_existing_school_exam_numbers(
        username,
        exam_id,
    )

    new_numbers = [
        number
        for number in submitted_numbers
        if number not in existing_numbers
    ]
    duplicate_numbers = [
        number
        for number in submitted_numbers
        if number in existing_numbers
    ]

    if not new_numbers:
        return {
            "saved": False,
            "new_numbers": [],
            "duplicate_numbers": duplicate_numbers,
            "message": "입력한 기출 오답번호가 모두 이미 저장되어 있습니다.",
        }

    (
        supabase.table("school_exam_wrong_answers")
        .insert(
            {
                "username": username,
                "exam_id": int(exam_id),
                "problem": format_problem_numbers(new_numbers),
                "memo": str(memo or "").strip(),
                "source_type": str(source_type or "manual").strip(),
                "source_filename": str(source_filename or "").strip(),
                "created_at": now_kst_iso(),
            }
        )
        .execute()
    )

    return {
        "saved": True,
        "new_numbers": new_numbers,
        "duplicate_numbers": duplicate_numbers,
        "message": "학교 기출 오답을 저장했습니다.",
    }

def get_school_exam_wrong_answers_df() -> pd.DataFrame:
    answer_rows = fetch_all_rows(
        "school_exam_wrong_answers",
        "id,username,exam_id,problem,memo,source_type,source_filename,created_at",
        order_column="id",
        desc=True,
    )
    exam_df = get_school_exam_master_df(active_only=False)

    columns = [
        "기록ID", "학생", "기출ID", "연도", "학교", "과목",
        "시험구분", "기출명", "문제번호", "비고",
        "입력방식", "원본파일", "작성일시",
    ]

    if not answer_rows:
        return pd.DataFrame(columns=columns)

    exam_map = {
        int(row["기출ID"]): row
        for _, row in exam_df.iterrows()
    }

    records = []

    for row in answer_rows:
        exam_id = int(row.get("exam_id"))
        exam = exam_map.get(exam_id, {})

        records.append(
            {
                "기록ID": row.get("id"),
                "학생": row.get("username", ""),
                "기출ID": exam_id,
                "연도": exam.get("연도", ""),
                "학교": exam.get("학교", ""),
                "과목": exam.get("과목", ""),
                "시험구분": exam.get("시험구분", ""),
                "기출명": exam.get("표시명", f"기출 ID {exam_id}"),
                "문제번호": row.get("problem", ""),
                "비고": row.get("memo", ""),
                "입력방식": (
                    "채점결과 파일"
                    if str(row.get("source_type", "")).strip() == "grading_file"
                    else "학생 직접 입력"
                ),
                "원본파일": row.get("source_filename", ""),
                "작성일시": row.get("created_at", ""),
            }
        )

    return pd.DataFrame(records, columns=columns)

def get_my_school_exam_wrong_answers(username: str) -> pd.DataFrame:
    df = get_school_exam_wrong_answers_df()

    if df.empty:
        return df

    return df[df["학생"] == username].copy()

def merge_school_exam_answers_for_paper(
    df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "학생명", "연도", "학교", "과목", "시험구분",
        "기출명", "문제번호", "비고", "PDF상단제목", "파일명",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    records = []

    grouped = df.groupby(
        ["학생", "연도", "학교", "과목", "시험구분", "기출명"],
        sort=False,
        dropna=False,
    )

    for (
        student,
        year,
        school,
        subject,
        exam_type,
        exam_name,
    ), group in grouped:
        numbers = []
        memos = []

        for _, row in group.iterrows():
            for number in parse_problem_numbers(row["문제번호"]):
                if number not in numbers:
                    numbers.append(number)

            memo = str(row.get("비고", "") or "").strip()
            if memo and memo not in memos:
                memos.append(memo)

        title = f"{year} {subject} {school} {exam_type} 학교 기출 오답 Paper"

        records.append(
            {
                "학생명": student,
                "연도": year,
                "학교": school,
                "과목": subject,
                "시험구분": exam_type,
                "기출명": exam_name,
                "문제번호": format_problem_numbers(numbers),
                "비고": " / ".join(memos),
                "PDF상단제목": title,
                "파일명": (
                    f"[학교기출오답][{school}][{student}]"
                    f"[{year}_{subject}_{exam_type}].pdf"
                ),
            }
        )

    return pd.DataFrame(records, columns=columns)

def _grade_cell_text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()

def _normalize_grade_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).strip()

def _extract_question_header(value) -> int | None:
    raw = _grade_cell_text(value)
    if not raw:
        return None

    if re.fullmatch(r"\d{1,3}(?:\.0)?", raw):
        number = int(float(raw))
        return number if 1 <= number <= 300 else None

    match = re.fullmatch(
        r"(?:문항\s*)?(\d{1,3})\s*(?:번|문항)?",
        raw,
        flags=re.I,
    )
    if match:
        number = int(match.group(1))
        return number if 1 <= number <= 300 else None

    return None

def _is_wrong_grade_mark(value) -> bool:
    raw = _grade_cell_text(value)
    if not raw:
        return False

    compact = re.sub(r"\s+", "", raw).upper()

    wrong_values = {
        "X", "×", "✕", "✗", "FALSE", "F", "N", "NO",
        "오답", "틀림", "틀린", "0", "미정답", "미응답",
    }
    correct_values = {
        "O", "○", "◯", "⭕", "TRUE", "T", "Y", "YES",
        "정답", "맞음", "1",
    }

    if compact in wrong_values:
        return True
    if compact in correct_values:
        return False

    # X 표시가 섞여 있는 경우
    if any(mark in compact for mark in ["×", "✕", "✗"]):
        return True

    return False

def parse_grading_filename(filename: str) -> dict:
    stem = Path(str(filename or "")).stem
    cleaned = re.sub(
        r"[_\-\s]*채점\s*결과.*$",
        "",
        stem,
        flags=re.I,
    ).strip()

    year = None
    year_match = re.search(r"(?<!\d)(20\d{2}|\d{2})\s*년도?", cleaned)
    if year_match:
        year = int(year_match.group(1))
        if year < 100:
            year += 2000

    school = ""
    school_match = re.search(
        r"([가-힣A-Za-z0-9]+?(?:여자고|여고|외고|고))",
        cleaned,
    )
    if school_match:
        school = school_match.group(1).strip()

    known_subjects = [
        "공통수학1", "공통수학2", "미적분1", "미적분2",
        "대수", "기하", "확률과통계", "확통",
    ]
    subject = next(
        (subject for subject in known_subjects if subject in cleaned),
        "",
    )

    exam_type = ""
    if school_match:
        tail = cleaned[school_match.end():].strip(" _-")
        if subject:
            tail = tail.replace(subject, "").strip(" _-")
        exam_type = tail.strip()

    if not exam_type:
        round_match = re.search(r"(\d+\s*회)", cleaned)
        if round_match:
            exam_type = re.sub(r"\s+", "", round_match.group(1))

    return {
        "year": year or 2025,
        "school": school,
        "subject": subject,
        "exam_type": exam_type or "1회",
    }

def _detect_grade_header_row(raw_df: pd.DataFrame) -> int | None:
    best_index = None
    best_score = -1

    scan_rows = min(len(raw_df), 40)

    for row_index in range(scan_rows):
        row_values = [
            _grade_cell_text(value)
            for value in raw_df.iloc[row_index].tolist()
        ]

        normalized = {
            re.sub(r"\s+", "", value)
            for value in row_values
            if value
        }

        has_name = any(
            re.sub(r"\s+", "", alias) in normalized
            for alias in GRADE_NAME_ALIASES
        )
        has_wrong_summary = any(
            re.sub(r"\s+", "", alias) in normalized
            for alias in GRADE_WRONG_SUMMARY_ALIASES
        )
        has_pattern = any(
            re.sub(r"\s+", "", alias) in normalized
            for alias in GRADE_PATTERN_ALIASES
        )
        question_count = sum(
            1 for value in row_values
            if _extract_question_header(value) is not None
        )

        score = (
            (12 if has_name else 0)
            + (8 if has_wrong_summary else 0)
            + (6 if has_pattern else 0)
            + min(question_count, 12)
        )

        if has_name and score > best_score:
            best_score = score
            best_index = row_index

    return best_index

def _make_unique_headers(values: list) -> list[str]:
    result = []
    seen = {}

    for index, value in enumerate(values):
        header = _grade_cell_text(value) or f"열{index + 1}"
        count = seen.get(header, 0)
        seen[header] = count + 1
        if count:
            header = f"{header}_{count + 1}"
        result.append(header)

    return result

def _resolve_grade_student(
    raw_name: str,
    current_teacher: str,
) -> tuple[str, str]:
    raw_name = str(raw_name or "").strip()

    if not raw_name:
        return "", "학생명 없음"

    users_df = get_all_users()
    roster_df = get_roster_df()

    user_names = (
        users_df["학생"].dropna().astype(str).str.strip().tolist()
        if not users_df.empty
        else []
    )
    roster_names = (
        roster_df["학생명"].dropna().astype(str).str.strip().tolist()
        if not roster_df.empty
        else []
    )

    all_candidates = list(dict.fromkeys(user_names + roster_names))
    raw_norm = _normalize_grade_name(raw_name)

    exact = [
        candidate
        for candidate in all_candidates
        if _normalize_grade_name(candidate) == raw_norm
    ]

    if len(exact) == 1:
        candidate = exact[0]
    else:
        contained = [
            candidate
            for candidate in all_candidates
            if len(_normalize_grade_name(candidate)) >= 2
            and (
                _normalize_grade_name(candidate) in raw_norm
                or raw_norm in _normalize_grade_name(candidate)
            )
        ]
        contained = list(dict.fromkeys(contained))

        if len(contained) == 1:
            candidate = contained[0]
        elif len(contained) > 1:
            return "", "학생명 중복·모호"
        else:
            return "", "명단에서 찾지 못함"

    if candidate not in user_names:
        return candidate, "미가입 계정"

    if current_teacher != ALL_TEACHER_ADMIN:
        allowed_students = set(
            roster_df.loc[
                roster_df["담당선생님"].apply(normalize_teacher_name)
                == normalize_teacher_name(current_teacher),
                "학생명",
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

        if candidate not in allowed_students:
            return candidate, "담당학생 아님"

    return candidate, "반영 가능"

def _find_split_ox_question_row(
    raw_df: pd.DataFrame,
    header_row: int,
) -> tuple[int | None, list[tuple[int, int]]]:
    """
    2단 헤더 채점결과를 인식합니다.

    예:
        1행: 이미지 | 성명 | ... | 문항별 OX | (병합/빈칸...)
        2행:                            1 | 2 | 3 | ... | 22
        3행: 학생A                     O | O | X | ...
    """
    max_scan_row = min(len(raw_df), header_row + 5)
    best_row = None
    best_questions = []

    for row_index in range(header_row + 1, max_scan_row):
        questions = []

        for col_index in range(raw_df.shape[1]):
            question_number = _extract_question_header(
                raw_df.iat[row_index, col_index]
            )

            if question_number is not None:
                questions.append((col_index, question_number))

        # 문항번호가 여러 개 연속해서 존재하는 행만 OX 문항 헤더로 인정
        if len(questions) >= 3:
            # 실제 시험 문항처럼 번호가 증가하는지 확인
            numbers = [number for _, number in questions]
            increasing_pairs = sum(
                1
                for left, right in zip(numbers, numbers[1:])
                if right > left
            )

            if increasing_pairs >= max(1, len(numbers) - 2):
                if len(questions) > len(best_questions):
                    best_row = row_index
                    best_questions = questions

    return best_row, best_questions

def _find_grade_name_column(
    raw_df: pd.DataFrame,
    header_row: int,
) -> int | None:
    aliases = {
        re.sub(r"\s+", "", alias)
        for alias in GRADE_NAME_ALIASES
    }

    for col_index in range(raw_df.shape[1]):
        value = re.sub(
            r"\s+",
            "",
            _grade_cell_text(raw_df.iat[header_row, col_index]),
        )

        if value in aliases:
            return col_index

    return None

def _find_grade_summary_columns(
    raw_df: pd.DataFrame,
    header_row: int,
) -> tuple[list[int], list[int]]:
    wrong_aliases = {
        re.sub(r"\s+", "", alias)
        for alias in GRADE_WRONG_SUMMARY_ALIASES
    }
    pattern_aliases = {
        re.sub(r"\s+", "", alias)
        for alias in GRADE_PATTERN_ALIASES
    }

    wrong_columns = []
    pattern_columns = []

    for col_index in range(raw_df.shape[1]):
        value = re.sub(
            r"\s+",
            "",
            _grade_cell_text(raw_df.iat[header_row, col_index]),
        )

        if value in wrong_aliases:
            wrong_columns.append(col_index)

        if value in pattern_aliases:
            pattern_columns.append(col_index)

    return wrong_columns, pattern_columns

def _row_has_any_ox_mark(
    raw_df: pd.DataFrame,
    row_index: int,
    question_columns: list[tuple[int, int]],
) -> bool:
    valid_marks = {
        "O", "○", "◯", "⭕",
        "X", "×", "✕", "✗",
    }

    for col_index, _ in question_columns:
        value = re.sub(
            r"\s+",
            "",
            _grade_cell_text(raw_df.iat[row_index, col_index]),
        ).upper()

        if value in valid_marks:
            return True

    return False

def analyze_grading_result_file(
    uploaded_file,
    current_teacher: str,
) -> tuple[pd.DataFrame, dict]:
    filename = str(uploaded_file.name)
    extension = Path(filename).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    if extension == ".xls":
        engine = "xlrd"
    elif extension == ".xlsx":
        engine = "openpyxl"
    else:
        raise ValueError("채점결과 파일은 .xls 또는 .xlsx만 지원합니다.")

    try:
        sheets = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=None,
            header=None,
            engine=engine,
            dtype=object,
        )
    except ImportError as error:
        if extension == ".xls":
            raise ValueError(
                "구형 .xls 파일을 읽으려면 requirements.txt에 "
                "'xlrd==2.0.1'을 추가해야 합니다."
            ) from error
        raise
    except Exception as error:
        raise ValueError(
            f"채점결과 파일을 읽지 못했습니다: {error}"
        ) from error

    records = []
    detected_question_max = 0
    parsed_sheet_count = 0
    detected_ox_rows = 0
    detected_ox_cells = 0

    for sheet_name, raw_df in sheets.items():
        if raw_df is None or raw_df.empty:
            continue

        header_row = _detect_grade_header_row(raw_df)
        if header_row is None:
            continue

        # --------------------------------------------------------
        # 1. 성명 열을 실제 열 번호로 찾기
        # --------------------------------------------------------
        name_col_index = _find_grade_name_column(
            raw_df,
            header_row,
        )

        if name_col_index is None:
            continue

        # --------------------------------------------------------
        # 2. 2단 헤더 구조 감지
        #
        # 1행: 성명 ... 문항별 OX
        # 2행:           1 2 3 4 ... 22
        # 3행~: 학생별 O / X
        # --------------------------------------------------------
        question_row, split_question_columns = (
            _find_split_ox_question_row(
                raw_df,
                header_row,
            )
        )

        wrong_summary_columns, pattern_columns = (
            _find_grade_summary_columns(
                raw_df,
                header_row,
            )
        )

        if question_row is not None and split_question_columns:
            data_start_row = question_row + 1
            question_columns = split_question_columns
        else:
            # ----------------------------------------------------
            # 기존 1단 헤더 파일도 계속 지원
            # ----------------------------------------------------
            data_start_row = header_row + 1
            question_columns = []

            for col_index in range(raw_df.shape[1]):
                question_number = _extract_question_header(
                    raw_df.iat[header_row, col_index]
                )

                if question_number is not None:
                    question_columns.append(
                        (col_index, question_number)
                    )

        if question_columns:
            detected_question_max = max(
                detected_question_max,
                max(
                    question_number
                    for _, question_number in question_columns
                ),
            )

        parsed_sheet_count += 1

        # --------------------------------------------------------
        # 3. 학생 행을 직접 열 인덱스로 읽기
        # --------------------------------------------------------
        for row_index in range(data_start_row, len(raw_df)):
            raw_student = _grade_cell_text(
                raw_df.iat[row_index, name_col_index]
            )

            if not raw_student:
                continue

            if any(
                token in raw_student
                for token in ["합계", "평균", "총점", "전체"]
            ):
                continue

            wrong_numbers = []

            # ----------------------------------------------------
            # A. 오답번호 열이 따로 있는 파일
            # ----------------------------------------------------
            if wrong_summary_columns:
                summary_value = _grade_cell_text(
                    raw_df.iat[
                        row_index,
                        wrong_summary_columns[0],
                    ]
                )

                wrong_numbers = parse_problem_numbers(
                    summary_value
                )

            # ----------------------------------------------------
            # B. 정오표 문자열이 한 셀에 들어간 파일
            # ----------------------------------------------------
            if not wrong_numbers and pattern_columns:
                pattern_value = _grade_cell_text(
                    raw_df.iat[
                        row_index,
                        pattern_columns[0],
                    ]
                )

                symbols = [
                    char
                    for char in pattern_value
                    if char not in {
                        " ", ",", "|", "/", "-", "_",
                    }
                ]

                wrong_numbers = [
                    str(index + 1)
                    for index, symbol in enumerate(symbols)
                    if _is_wrong_grade_mark(symbol)
                ]

                if symbols:
                    detected_question_max = max(
                        detected_question_max,
                        len(symbols),
                    )

            # ----------------------------------------------------
            # C. 네 파일 구조:
            #    문항번호 열의 같은 위치에서 X만 오답 처리
            # ----------------------------------------------------
            if question_columns:
                row_has_ox = _row_has_any_ox_mark(
                    raw_df,
                    row_index,
                    question_columns,
                )

                if row_has_ox:
                    detected_ox_rows += 1

                ox_wrong_numbers = []

                for col_index, question_number in question_columns:
                    cell_value = _grade_cell_text(
                        raw_df.iat[row_index, col_index]
                    )

                    compact_value = re.sub(
                        r"\s+",
                        "",
                        cell_value,
                    ).upper()

                    if compact_value in {
                        "O", "○", "◯", "⭕",
                        "X", "×", "✕", "✗",
                    }:
                        detected_ox_cells += 1

                    # X만 오답으로 처리
                    if _is_wrong_grade_mark(cell_value):
                        ox_wrong_numbers.append(
                            str(question_number)
                        )

                # 문항별 O/X가 실제로 존재하면
                # 다른 방식보다 이 결과를 최우선으로 사용
                if row_has_ox:
                    wrong_numbers = ox_wrong_numbers

            wrong_numbers = list(
                dict.fromkeys(wrong_numbers)
            )

            matched_student, status = _resolve_grade_student(
                raw_student,
                current_teacher,
            )

            if not wrong_numbers and status == "반영 가능":
                status = "오답 없음"

            records.append(
                {
                    "시트": str(sheet_name),
                    "원본학생명": raw_student,
                    "매칭학생": matched_student,
                    "오답번호": format_problem_numbers(
                        wrong_numbers
                    ),
                    "오답개수": len(wrong_numbers),
                    "상태": status,
                }
            )

    if not records:
        raise ValueError(
            "학생명과 오답 문항을 자동 인식하지 못했습니다. "
            "파일의 성명 열과 문항별 O/X 영역을 확인해주세요."
        )

    preview_df = pd.DataFrame(records)

    # ------------------------------------------------------------
    # 안전장치:
    # 문항번호는 인식했는데 O/X 셀을 하나도 못 읽은 경우
    # DB 반영 전 분석 실패로 처리
    # ------------------------------------------------------------
    if detected_question_max > 0 and detected_ox_cells == 0:
        raise ValueError(
            "문항번호는 인식했지만 학생별 O/X 값을 읽지 못했습니다. "
            "원본 파일의 '문항별 OX' 영역을 확인해주세요."
        )

    info = {
        "sheet_count": parsed_sheet_count,
        "question_count": detected_question_max or None,
        "detected_ox_rows": detected_ox_rows,
        "detected_ox_cells": detected_ox_cells,
        "file_hash": hashlib.sha256(file_bytes).hexdigest(),
        "file_name": filename,
        "file_size": len(file_bytes),
    }

    return preview_df, info

def get_grade_import_by_hash(file_hash: str) -> dict | None:
    response = (
        supabase.table("school_exam_grade_imports")
        .select(
            "id,file_hash,file_name,exam_id,uploader,"
            "imported_students,imported_numbers,skipped_students,created_at"
        )
        .eq("file_hash", str(file_hash))
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

def ensure_school_exam_for_grade_import(
    exam_year: int,
    school_name: str,
    subject: str,
    exam_type: str,
    question_count: int | None = None,
) -> int:
    exam_year = int(exam_year)
    school_name = str(school_name or "").strip()
    subject = str(subject or "").strip()
    exam_type = str(exam_type or "").strip()

    if not school_name or not subject or not exam_type:
        raise ValueError("연도·학교·과목·시험구분을 모두 확인해주세요.")

    response = (
        supabase.table("school_exam_master")
        .select("id")
        .eq("exam_year", exam_year)
        .eq("school_name", school_name)
        .eq("subject", subject)
        .eq("exam_type", exam_type)
        .limit(1)
        .execute()
    )

    if response.data:
        return int(response.data[0]["id"])

    display_name = make_school_exam_display_name(
        exam_year,
        school_name,
        subject,
        exam_type,
    )

    insert_response = (
        supabase.table("school_exam_master")
        .insert(
            {
                "exam_year": exam_year,
                "school_name": school_name,
                "subject": subject,
                "exam_type": exam_type,
                "question_count": (
                    int(question_count)
                    if question_count
                    else None
                ),
                "scope": "",
                "display_name": display_name,
                "is_active": True,
                "created_at": now_kst_iso(),
            }
        )
        .execute()
    )

    if not insert_response.data:
        raise RuntimeError("학교 기출 시험 등록에 실패했습니다.")

    return int(insert_response.data[0]["id"])

def import_grading_preview_to_school_exam(
    preview_df: pd.DataFrame,
    file_info: dict,
    exam_year: int,
    school_name: str,
    subject: str,
    exam_type: str,
    current_teacher: str,
    question_count: int | None = None,
) -> dict:
    duplicate = get_grade_import_by_hash(
        file_info["file_hash"]
    )

    if duplicate:
        raise ValueError(
            "이 채점결과 파일은 이미 반영된 파일입니다. "
            f"기존 업로드: {duplicate.get('created_at', '')}"
        )

    exam_id = ensure_school_exam_for_grade_import(
        exam_year,
        school_name,
        subject,
        exam_type,
        question_count,
    )

    imported_students = 0
    imported_numbers = 0
    skipped_students = 0

    valid_df = preview_df[
        preview_df["상태"].isin(["반영 가능", "오답 없음"])
    ].copy()

    for _, row in valid_df.iterrows():
        username = str(row["매칭학생"]).strip()
        problem_number = str(row["오답번호"] or "").strip()

        if not username:
            skipped_students += 1
            continue

        if not problem_number:
            # 오답이 없는 학생은 기록을 만들지 않습니다.
            continue

        result = add_school_exam_wrong_answer(
            username=username,
            exam_id=exam_id,
            problem_number=problem_number,
            memo="채점결과 파일 자동 반영",
            source_type="grading_file",
            source_filename=file_info["file_name"],
        )

        if result["saved"]:
            imported_students += 1
            imported_numbers += len(result["new_numbers"])
        else:
            skipped_students += 1

    skipped_students += int(
        (~preview_df["상태"].isin(["반영 가능", "오답 없음"])).sum()
    )

    (
        supabase.table("school_exam_grade_imports")
        .insert(
            {
                "file_hash": file_info["file_hash"],
                "file_name": file_info["file_name"],
                "exam_id": int(exam_id),
                "uploader": str(current_teacher or "").strip(),
                "imported_students": int(imported_students),
                "imported_numbers": int(imported_numbers),
                "skipped_students": int(skipped_students),
                "created_at": now_kst_iso(),
            }
        )
        .execute()
    )

    return {
        "exam_id": exam_id,
        "imported_students": imported_students,
        "imported_numbers": imported_numbers,
        "skipped_students": skipped_students,
    }

def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="오답현황")

    output.seek(0)
    return output.getvalue()

def get_all_users() -> pd.DataFrame:
    user_rows = fetch_all_rows(
        "users",
        "username,grade,created_at",
        order_column="created_at",
        desc=True
    )

    if not user_rows:
        return pd.DataFrame(
            columns=["학생", "학년", "가입일시", "오답개수"]
        )

    answer_rows = fetch_all_rows("wrong_answers", "username")
    answer_counts = Counter(
        row.get("username", "")
        for row in answer_rows
        if row.get("username")
    )

    records = []

    for row in user_rows:
        username = row.get("username", "")
        records.append(
            {
                "학생": username,
                "학년": row.get("grade") or "미지정",
                "가입일시": row.get("created_at", ""),
                "오답개수": answer_counts.get(username, 0)
            }
        )

    return pd.DataFrame(records)

def delete_user(username: str, delete_answers: bool = True):
    """
    users → wrong_answers 외래키가 ON DELETE CASCADE로 설정되어 있으므로,
    계정을 삭제하면 해당 학생의 오답 기록도 함께 삭제됩니다.
    """
    if delete_answers:
        (
            supabase.table("wrong_answers")
            .delete()
            .eq("username", username)
            .execute()
        )

    (
        supabase.table("users")
        .delete()
        .eq("username", username)
        .execute()
    )

def reset_user_password(username: str, new_password: str):
    (
        supabase.table("users")
        .update(
            {
                "password_hash": hash_pw(new_password),
                "temp_password": new_password
            }
        )
        .eq("username", username)
        .execute()
    )

def update_user_grade(username: str, new_grade: str):
    (
        supabase.table("users")
        .update({"grade": new_grade})
        .eq("username", username)
        .execute()
    )

def username_exists(username: str, exclude_username: str | None = None) -> bool:
    """users 테이블에서 학생 이름의 중복 여부를 확인합니다."""
    username = str(username or "").strip()

    if not username:
        return False

    response = (
        supabase.table("users")
        .select("username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    return username != str(exclude_username or "").strip()

def rename_student_everywhere(old_name: str, new_name: str) -> dict:
    """
    외래키 제약을 안전하게 지키면서 학생 이름을 변경합니다.

    처리 순서:
    1. 기존 users 계정 정보를 읽음
    2. 새 이름의 users 계정을 먼저 생성
    3. wrong_answers와 student_roster를 새 이름으로 변경
    4. 기존 users 계정 삭제

    users.username을 먼저 수정하면 wrong_answers 외래키 때문에
    PostgreSQL 오류 23503이 발생하므로 이 순서를 사용합니다.
    """
    old_name = str(old_name or "").strip()
    new_name = str(new_name or "").strip()

    if not old_name or not new_name:
        raise ValueError("현재 이름과 새 이름을 모두 입력해주세요.")

    if old_name == new_name:
        raise ValueError("현재 이름과 새 이름이 같습니다.")

    # 새 이름 중복 확인
    existing_new_user = (
        supabase.table("users")
        .select("username")
        .eq("username", new_name)
        .limit(1)
        .execute()
    )
    if existing_new_user.data:
        raise ValueError("새 이름으로 이미 가입된 학생 계정이 있습니다.")

    existing_new_roster = (
        supabase.table("student_roster")
        .select("id")
        .eq("student_name", new_name)
        .limit(1)
        .execute()
    )
    if existing_new_roster.data:
        raise ValueError(
            "새 이름과 동일한 학생이 명단에 이미 있습니다. "
            "동명이인이라면 이름 뒤에 숫자 등을 붙여 구분해주세요."
        )

    # 기존 계정 정보 읽기
    old_user_response = (
        supabase.table("users")
        .select("username,password_hash,grade,temp_password,created_at")
        .eq("username", old_name)
        .limit(1)
        .execute()
    )

    old_user = old_user_response.data[0] if old_user_response.data else None

    # 계정이 없는 학생도 명단/오답 이름 수정은 가능하게 처리
    new_user_created = False

    try:
        # 1) 새 부모(users) 행을 먼저 생성
        if old_user:
            new_user_payload = {
                "username": new_name,
                "password_hash": old_user.get("password_hash", ""),
                "grade": old_user.get("grade") or "미지정",
                "temp_password": old_user.get("temp_password") or "",
                "created_at": old_user.get("created_at") or now_kst_iso(),
            }

            (
                supabase.table("users")
                .insert(new_user_payload)
                .execute()
            )
            new_user_created = True

        # 2) 자식 테이블을 새 이름으로 이동
        answer_response = (
            supabase.table("wrong_answers")
            .update({"username": new_name})
            .eq("username", old_name)
            .execute()
        )

        roster_response = (
            supabase.table("student_roster")
            .update({"student_name": new_name})
            .eq("student_name", old_name)
            .execute()
        )

        # 3) 기존 부모(users) 행 삭제
        deleted_users = 0
        if old_user:
            delete_response = (
                supabase.table("users")
                .delete()
                .eq("username", old_name)
                .execute()
            )
            deleted_users = len(delete_response.data or [])

        return {
            "users_created": 1 if new_user_created else 0,
            "users_deleted": deleted_users,
            "wrong_answers": len(answer_response.data or []),
            "student_roster": len(roster_response.data or []),
        }

    except Exception:
        # 중간 실패 시 새 계정만 생성된 상태라면 가능한 범위에서 롤백
        # 자식 데이터가 이미 새 이름으로 이동한 경우에는 새 계정을 지우면
        # 다시 외래키 오류가 발생할 수 있으므로 현재 상태를 보존합니다.
        try:
            moved_answer_check = (
                supabase.table("wrong_answers")
                .select("id")
                .eq("username", new_name)
                .limit(1)
                .execute()
            )

            if new_user_created and not moved_answer_check.data:
                (
                    supabase.table("users")
                    .delete()
                    .eq("username", new_name)
                    .execute()
                )
        except Exception:
            pass

        raise

def update_roster_record(
    record_id: int,
    *,
    teacher_name: str,
    class_name: str,
    school_name: str,
    grade: str,
    book_name: str,
):
    """선택한 수강 등록 행의 담당 선생님·반·학교·학년·교재를 변경합니다."""
    payload = {
        "teacher_name": str(teacher_name or "").strip(),
        "class_name": str(class_name or "").strip(),
        "school_name": str(school_name or "").strip(),
        "grade": str(grade or "").strip(),
        "book_name": str(book_name or "").strip(),
    }

    if not payload["teacher_name"]:
        raise ValueError("담당 선생님을 선택해주세요.")
    if not payload["class_name"]:
        raise ValueError("반명을 입력해주세요.")
    if not payload["school_name"]:
        raise ValueError("학교명을 입력해주세요.")
    if not payload["grade"]:
        raise ValueError("학년을 선택해주세요.")
    if not payload["book_name"]:
        raise ValueError("교재를 선택해주세요.")

    (
        supabase.table("student_roster")
        .update(payload)
        .eq("id", int(record_id))
        .execute()
    )

def update_student_grade_everywhere(username: str, new_grade: str):
    """학생 계정 학년과 명단에 등록된 모든 학년을 함께 변경합니다."""
    username = str(username or "").strip()
    new_grade = str(new_grade or "").strip()

    (
        supabase.table("users")
        .update({"grade": new_grade})
        .eq("username", username)
        .execute()
    )

    (
        supabase.table("student_roster")
        .update({"grade": new_grade})
        .eq("student_name", username)
        .execute()
    )

def delete_student_management(
    username: str,
    *,
    delete_user_account: bool,
    delete_roster: bool,
    delete_answers: bool,
) -> dict:
    """선택 옵션에 따라 학생 계정·명단·오답 기록을 삭제합니다."""
    username = str(username or "").strip()
    result = {
        "users": 0,
        "student_roster": 0,
        "wrong_answers": 0,
    }

    if delete_answers:
        response = (
            supabase.table("wrong_answers")
            .delete()
            .eq("username", username)
            .execute()
        )
        result["wrong_answers"] = len(response.data or [])

    if delete_roster:
        response = (
            supabase.table("student_roster")
            .delete()
            .eq("student_name", username)
            .execute()
        )
        result["student_roster"] = len(response.data or [])

    if delete_user_account:
        response = (
            supabase.table("users")
            .delete()
            .eq("username", username)
            .execute()
        )
        result["users"] = len(response.data or [])

    return result

def get_account_wrong_answer_count(username: str) -> int:
    response = (
        supabase.table("wrong_answers")
        .select("id", count="exact")
        .eq("username", str(username or "").strip())
        .execute()
    )

    if getattr(response, "count", None) is not None:
        return int(response.count)

    return len(response.data or [])

def transfer_wrong_answers_between_accounts(
    old_username: str,
    new_username: str,
    *,
    delete_old_account: bool = False,
) -> dict:
    """
    이전 계정의 오답 기록을 새 계정으로 안전하게 이전합니다.

    - 새 계정에 이미 존재하는 동일 교재·문제번호는 중복 저장하지 않습니다.
    - 이전이 끝난 기존 오답 행은 삭제합니다.
    - 선택한 경우 오답이 모두 이전된 이전 계정도 삭제합니다.
    """
    old_username = str(old_username or "").strip()
    new_username = str(new_username or "").strip()

    if not old_username or not new_username:
        raise ValueError("이전 계정과 새 계정을 모두 선택해주세요.")

    if old_username == new_username:
        raise ValueError("이전 계정과 새 계정이 같습니다.")

    old_user = (
        supabase.table("users")
        .select("username")
        .eq("username", old_username)
        .limit(1)
        .execute()
    )

    new_user = (
        supabase.table("users")
        .select("username")
        .eq("username", new_username)
        .limit(1)
        .execute()
    )

    if not old_user.data:
        raise ValueError("이전 계정을 찾을 수 없습니다.")

    if not new_user.data:
        raise ValueError(
            "새 계정을 찾을 수 없습니다. "
            "학생이 새 이름으로 먼저 회원가입했는지 확인해주세요."
        )

    old_rows = fetch_all_rows(
        "wrong_answers",
        "id,unit,problem,memo,created_at",
        filters=[("username", "eq", old_username)],
        order_column="id",
        desc=False,
    )

    if not old_rows:
        raise ValueError("이전 계정에 옮길 오답 기록이 없습니다.")

    target_existing: dict[str, set[str]] = {}

    target_rows = fetch_all_rows(
        "wrong_answers",
        "unit,problem",
        filters=[("username", "eq", new_username)],
        order_column="id",
        desc=False,
    )

    for row in target_rows:
        book = str(row.get("unit", "")).strip()
        target_existing.setdefault(book, set()).update(
            parse_problem_numbers(row.get("problem", ""))
        )

    inserted_rows = 0
    deleted_rows = 0
    moved_numbers = 0
    skipped_duplicate_numbers = 0

    for row in old_rows:
        row_id = int(row["id"])
        book = str(row.get("unit", "")).strip()
        source_numbers = parse_problem_numbers(row.get("problem", ""))
        existing_numbers = target_existing.setdefault(book, set())

        new_numbers = [
            number
            for number in source_numbers
            if number not in existing_numbers
        ]

        skipped_duplicate_numbers += (
            len(source_numbers) - len(new_numbers)
        )

        if new_numbers:
            (
                supabase.table("wrong_answers")
                .insert(
                    {
                        "username": new_username,
                        "unit": book,
                        "problem": format_problem_numbers(new_numbers),
                        "memo": str(row.get("memo", "") or ""),
                        "created_at": (
                            row.get("created_at")
                            or now_kst_iso()
                        ),
                    }
                )
                .execute()
            )

            existing_numbers.update(new_numbers)
            moved_numbers += len(new_numbers)
            inserted_rows += 1

        # 새 계정에 이미 존재하는 문제까지 포함하여 이전 처리가 끝난 행 삭제
        (
            supabase.table("wrong_answers")
            .delete()
            .eq("id", row_id)
            .execute()
        )
        deleted_rows += 1

    old_account_deleted = False

    if delete_old_account:
        remaining = (
            supabase.table("wrong_answers")
            .select("id")
            .eq("username", old_username)
            .limit(1)
            .execute()
        )

        if remaining.data:
            raise ValueError(
                "이전 계정에 오답 기록이 남아 있어 계정을 삭제하지 않았습니다."
            )

        (
            supabase.table("users")
            .delete()
            .eq("username", old_username)
            .execute()
        )
        old_account_deleted = True

    cleanup_duplicate_wrong_answers()

    return {
        "inserted_rows": inserted_rows,
        "deleted_rows": deleted_rows,
        "moved_numbers": moved_numbers,
        "skipped_duplicate_numbers": skipped_duplicate_numbers,
        "old_account_deleted": old_account_deleted,
    }

def normalize_excel_datetime(value) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return now_kst_iso()

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return now_kst_iso()

    return parsed.to_pydatetime().replace(tzinfo=None).isoformat(timespec="seconds")

def restore_users_from_excel(
    uploaded_file,
    temporary_password: str = "sg2026"
):
    """
    회원목록 엑셀을 읽어 Supabase users 테이블에 계정을 일괄 복구합니다.

    지원 열:
    - 학생
    - 학년
    - 임시비밀번호
    - 기존가입일시
    """
    df = pd.read_excel(uploaded_file)

    required_columns = {"학생", "학년"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "필수 열이 없습니다: " + ", ".join(sorted(missing_columns))
        )

    existing_rows = fetch_all_rows("users", "username")
    existing_names = {
        row.get("username", "")
        for row in existing_rows
        if row.get("username")
    }

    restore_rows: list[dict] = []
    created_count = 0
    updated_count = 0
    skipped_count = 0
    restored_names: list[str] = []

    for _, row in df.iterrows():
        username = str(row.get("학생", "")).strip()

        if not username or username.lower() == "nan":
            skipped_count += 1
            continue

        grade_value = row.get("학년", "미지정")
        grade = (
            "미지정"
            if pd.isna(grade_value) or str(grade_value).strip() == ""
            else str(grade_value).strip()
        )

        password_value = row.get("임시비밀번호", temporary_password)
        password = (
            temporary_password
            if pd.isna(password_value) or str(password_value).strip() == ""
            else str(password_value).strip()
        )

        created_at = normalize_excel_datetime(
            row.get("기존가입일시", "")
        )

        restore_rows.append(
            {
                "username": username,
                "password_hash": hash_pw(password),
                "grade": grade,
                "temp_password": password,
                "created_at": created_at
            }
        )

        if username in existing_names:
            updated_count += 1
        else:
            created_count += 1

        restored_names.append(username)

    if restore_rows:
        (
            supabase.table("users")
            .upsert(restore_rows, on_conflict="username")
            .execute()
        )

    return {
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "total": created_count + updated_count,
        "names": restored_names
    }
