"""UC2 올리기 전 점검: GPU 판독 결과를 경고 카드와 가릴 영역으로 바꾼다."""
from app.schemas.contracts import AnalyzeResult, CheckResponse, Clue, Region, Warning, risk_level
from app.services.engine import TYPE_LABEL, TYPE_ORDER
from app.services.text_rules import TIME_RE

ACTION = {
    "name": "이름표 가리기, 이름 해시태그 빼기",
    "age": "나이 표현 빼기",
    "school": "유치원·반 이름 가리기",
    "area": "간판·표지판 가리기, 위치 태그 빼기",
    "time": "시간 표현 빼기",
}


def _severity(t: str, types: set[str]) -> str:
    if t == "age":
        return "medium"
    if t == "time" and "name" not in types:
        return "medium"
    return "high"


def build(result: AnalyzeResult, caption: str, prior: list[Clue], image_size: tuple[int, int]) -> CheckResponse:
    prior_types = {c.type for c in prior}
    new_types = {e.type for e in result.entities}
    all_types = prior_types | new_types

    regions: list[Region] = []
    for e in result.entities:
        if e.box:
            regions.append(Region(id=f"r{len(regions) + 1}", type=e.type, text=e.value, box=e.box))
    known = {tuple(r.box) for r in regions}
    for t in result.texts:  # 단서로 판단되지 않았지만 읽힌 글자 = 확인 필요
        if t.box and tuple(t.box) not in known and t.source != "caption" and (t.conf is not None and t.conf < 0.6):
            regions.append(Region(id=f"r{len(regions) + 1}", type="unreadable", text=t.text, box=t.box))

    warnings: list[Warning] = []
    for t in TYPE_ORDER:
        ents = [e for e in result.entities if e.type == t]
        if not ents:
            continue
        values = ", ".join(dict.fromkeys(e.value for e in ents))
        where = " · ".join(sorted({"사진" if e.evidence == "image" else "캡션" for e in ents}))
        image_values = [e.value for e in ents if e.evidence == "image"]
        in_caption = any(v and v in caption for v in image_values)
        why = f"{where}에 {TYPE_LABEL[t]} \"{values}\""
        if t not in prior_types and prior_types:
            why += " · 이전 게시물의 단서와 이어져요"
        if in_caption:
            why += " · 사진을 가려도 캡션에 그대로 있어요"
        warnings.append(
            Warning(
                type=t,
                severity=_severity(t, all_types),
                why=why,
                action=ACTION[t],
                region_ids=[r.id for r in regions if r.type == t],
                in_caption=in_caption,
            )
        )
    unreadable = [r for r in regions if r.type == "unreadable"]
    if unreadable:
        warnings.append(
            Warning(
                type="unreadable",
                severity="check",
                why=f"읽기가 확실하지 않은 글자 {len(unreadable)}곳",
                action="직접 확인 후 필요하면 가리기",
                region_ids=[r.id for r in unreadable],
            )
        )

    suggestion = caption
    for e in result.entities:
        if e.evidence != "caption" or not e.value:
            continue
        if e.type == "time":
            suggestion = TIME_RE.sub("", suggestion)
        else:
            suggestion = suggestion.replace(f"#{e.value}이", "").replace(f"#{e.value}", "").replace(e.value, "")
    suggestion = " ".join(suggestion.replace(" 에 ", " ").split())

    return CheckResponse(
        level_now=risk_level(prior_types) if prior else None,
        level_if_posted=risk_level(all_types),
        added=[t for t in TYPE_ORDER if t in new_types and t not in prior_types],
        warnings=warnings,
        regions=regions,
        caption_suggestion=suggestion,
        image_size=list(image_size),
    )
