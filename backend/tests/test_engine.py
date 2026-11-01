from app.schemas.contracts import Entity
from app.services import engine


def E(t, v, ev="image"):
    return Entity(type=t, value=v, evidence=ev)


def test_link_and_minimal_cleanup():
    posts = {
        "p1": [E("name", "하늘"), E("school", "햇살유치원")],
        "p2": [E("area", "개포동", "caption"), E("time", "8:40", "caption")],
        "p3": [E("name", "하늘", "caption"), E("age", "5살", "caption")],
        "p4": [],
    }
    meta = {p: {"caption": "", "photo_ids": [f"{p}_1"]} for p in posts}
    r = engine.build_result(posts, meta, [])
    assert r.level == "very_high"
    assert r.reason[0] == "name" and r.reason[-1] == "time"
    assert r.card["name"] == "하늘"
    assert set(r.sources["name"]) == {"p1", "p3"}
    # 2개만 정리하면 '이름 + 장소' 조합이 끊겨 '주의' (p1+p3 또는 p1+p2 모두 최소)
    assert len(r.cleanup) == 2 and "p1" in r.cleanup
    assert r.level_after_cleanup == "caution"
    assert all(item.cuts for item in r.cleanup_items)


def test_safe_and_caution_need_no_cleanup():
    assert engine.build_result({"p1": []}, {}, []).level == "safe"
    r = engine.build_result({"p1": [E("name", "하늘")]}, {}, [])
    assert r.level == "caution" and r.cleanup == []


def test_explanation_text():
    assert "언제 어디서" in engine.explain(["name", "school", "time"], "very_high")
    assert engine.explain([], "safe") == "아이를 특정할 단서가 없어요."


def test_caption_edits_split_clues():
    from app.schemas.contracts import AnalyzeResult
    from app.services.precheck import apply_edits, caption_edits
    from app.services.text_rules import caption_entities

    cap = "오늘도 8시 40분에 등원 완료 #하늘이"
    edits = caption_edits(AnalyzeResult(photo_id="p", texts=[], entities=caption_entities(cap)), cap)
    assert [(e.type, e.text) for e in edits] == [("time", "8시 40분에"), ("name", "#하늘이")]
    assert apply_edits(cap, [e.text for e in edits]) == "오늘도 등원 완료"
