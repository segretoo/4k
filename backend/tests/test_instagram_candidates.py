from app.services.text_rules import caption_candidates


def test_location_hashtag_is_not_also_suggested_as_a_name():
    candidates = caption_candidates("주말 산책 #망원동", "p001")

    assert [(item["type"], item["value"]) for item in candidates] == [("area", "망원동")]


def test_korean_name_hashtag_with_subject_suffix_is_not_duplicated():
    candidates = caption_candidates("오늘 하늘이랑 산책 #하늘이", "p002")

    names = [item["value"] for item in candidates if item["type"] == "name"]
    assert names == ["하늘"]
