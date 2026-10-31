from app.schemas.contracts import risk_level


def test_levels():
    assert risk_level(set()) == "safe"
    assert risk_level({"name", "age"}) == "caution"
    assert risk_level({"school", "time"}) == "caution"
    assert risk_level({"name", "school"}) == "high"
    assert risk_level({"name", "area"}) == "high"
    assert risk_level({"name", "school", "time"}) == "very_high"
