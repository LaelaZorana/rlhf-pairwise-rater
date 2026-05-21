from rater import stats


def _scores(h, hh, a, i):
    return {"helpfulness": h, "harmlessness": hh, "accuracy": a, "instruction_following": i}


def test_summary_basic():
    ratings = [
        {"id": "1", "preference": "A", "confidence": 4,
         "scores_a": _scores(5, 5, 5, 5), "scores_b": _scores(3, 3, 3, 3)},
        {"id": "2", "preference": "B", "confidence": 3,
         "scores_a": _scores(2, 5, 2, 2), "scores_b": _scores(4, 5, 4, 4)},
        {"id": "3", "preference": "TIE", "confidence": 2,
         "scores_a": _scores(3, 3, 3, 3), "scores_b": _scores(3, 3, 3, 3)},
    ]
    s = stats.summarize(ratings)
    assert s["total"] == 3
    assert s["preference_counts"] == {"A": 1, "B": 1, "TIE": 1}
    assert s["mean_confidence"] == 3.0
    assert s["self_consistency_flags"] == []


def test_self_consistency_flag():
    # Said A wins, but B scored higher on every axis. Should flag.
    bad = [{"id": "x", "preference": "A", "confidence": 5,
            "scores_a": _scores(1, 1, 1, 1),
            "scores_b": _scores(5, 5, 5, 5)}]
    s = stats.summarize(bad)
    assert s["self_consistency_flags"] == ["x"]


def test_kappa_perfect():
    k = stats.cohens_kappa(["A", "B", "A"], ["A", "B", "A"])
    assert k == 1.0


def test_kappa_no_better_than_chance():
    # Both raters always say A — kappa undefined / 1.0 by convention here
    k = stats.cohens_kappa(["A", "A", "A"], ["A", "A", "A"])
    assert k == 1.0


def test_kappa_disagree():
    k = stats.cohens_kappa(["A", "B", "A", "B"], ["B", "A", "B", "A"])
    assert k < 0  # worse than chance


def test_agreement_between_overlapping():
    r1 = [{"id": "1", "preference": "A", "confidence": 4, "scores_a": {}, "scores_b": {}},
          {"id": "2", "preference": "B", "confidence": 4, "scores_a": {}, "scores_b": {}}]
    r2 = [{"id": "1", "preference": "A", "confidence": 3, "scores_a": {}, "scores_b": {}},
          {"id": "2", "preference": "A", "confidence": 3, "scores_a": {}, "scores_b": {}},
          {"id": "3", "preference": "B", "confidence": 3, "scores_a": {}, "scores_b": {}}]
    a = stats.agreement_between(r1, r2)
    assert a["common_cases"] == 2
    assert a["disagreements"] == [("2", "B", "A")]
