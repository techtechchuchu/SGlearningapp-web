from backend.legacy import (
    build_paper_title,
    format_xpattern_display_numbers,
    parse_problem_numbers,
    split_roster_books,
)


def test_multi_book_roster_is_expanded():
    assert split_roster_books("X-패턴 공통수학2, UNIT N제 공통수학2") == [
        "X-패턴 공통수학2",
        "UNIT N제 공통수학2",
    ]


def test_problem_numbers_are_normalized_without_duplicates():
    assert parse_problem_numbers("12, 9 12") == ["12", "9"]


def test_xpattern_offset_returns_original_number():
    assert format_xpattern_display_numbers("X-패턴 공통수학2", "1212") == "12"


def test_paper_title_matches_streamlit_rule():
    assert build_paper_title(
        "이주백.T", "월금일(앞) 고1 내신심화반", "고1", "공통수학2 고쟁이", 9, 2
    ) == "이주백T 고1 공통수학2 오답 Paper - 9월 2주차"
