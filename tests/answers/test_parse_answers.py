from pipeline.answers.parse_answers import parse


def test_score_and_reason_are_read_after_thinking():
    text = '<think>{"visa_score": 10}</think> Answer: {"visa_score": 85, "reason": "No ground applies."}'
    assert parse(text)["visa_score"] == 85.0 and parse(text)["reason"] == "No ground applies."


def test_other_answer_formats():
    assert parse('{"risk_score": 30, "reason": "x"}', "risk")["visa_score"] == 70.0
    assert parse('{"recommendation": "Refuse", "reason": "x"}', "binary")["granted"] == 0
    assert parse('{"visa_score": 90}', "score_only")["status"] == "ok"


def test_answer_without_valid_value_is_unreadable():
    assert parse('{"visa_score": 140, "reason": "x"}')["status"] == "unreadable"
    assert parse('{"recommendation": "maybe", "reason": "x"}', "binary")["status"] == "unreadable"
