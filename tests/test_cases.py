from rater import cases


def test_append_rating_roundtrip(tmp_path):
    p = tmp_path / "r.jsonl"
    cases.append_rating(p, {"id": "001", "preference": "A"})
    cases.append_rating(p, {"id": "002", "preference": "B"})
    assert cases.read_ratings(p) == [
        {"id": "001", "preference": "A"},
        {"id": "002", "preference": "B"},
    ]
