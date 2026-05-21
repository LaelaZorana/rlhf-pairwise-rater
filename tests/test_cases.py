from pathlib import Path

from rater import cases


def test_read_skips_blank_lines(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text('{"id":"a","x":1}\n\n{"id":"b","x":2}\n', encoding="utf-8")
    items = list(cases.read_cases(p))
    assert [i["id"] for i in items] == ["a", "b"]


def test_append_rating_roundtrip(tmp_path):
    p = tmp_path / "r.jsonl"
    cases.append_rating(p, {"id": "001", "preference": "A"})
    cases.append_rating(p, {"id": "002", "preference": "B"})
    out = cases.read_ratings(p)
    assert out == [{"id": "001", "preference": "A"},
                   {"id": "002", "preference": "B"}]


def test_invalid_json_raises_with_line_number(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text('{"id":"a"}\n{not valid\n', encoding="utf-8")
    try:
        list(cases.read_cases(p))
    except ValueError as e:
        assert "line 2" in str(e)
    else:
        raise AssertionError("expected ValueError")
