"""UC2 올리기 전 점검: GPU 판독 결과를 경고 카드와 가릴 영역으로 바꾼다."""
import re

from app.schemas.contracts import AnalyzeResult, CaptionEdit, CheckResponse, Clue, Region, Warning, risk_level
from app.services.engine import TYPE_LABEL, TYPE_ORDER
from app.services.text_rules import TIME_RE

ACTION = {
    "name": "이름표 가리기, 이름 해시태그 빼기",
    "age": "나이 표현 빼기",
    "school": "유치원·반 이름 가리기",
    "area": "간판·표지판 가리기, 위치 태그 빼기",
    "time": "시간 표현 빼기",
    "contact": "전화번호·이메일 가리기",
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
            regions.append(Region(id=f"r{len(regions) + 1}", type=e.type, text=e.value, box=e.box,
                                  polygon=e.polygon, path=e.path))
    known = {tuple(r.box) for r in regions}
    for t in result.texts:  # 단서로 판단되지 않았지만 읽힌 글자 = 확인 필요
        if t.box and tuple(t.box) not in known and t.source != "caption" and (t.conf is not None and t.conf < 0.6):
            regions.append(Region(id=f"r{len(regions) + 1}", type="unreadable", text=t.text, box=t.box,
                                  polygon=t.polygon, path=t.path))

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

    edits = caption_edits(result, caption)
    suggestion = apply_edits(caption, [e.text for e in edits])

    return CheckResponse(
        level_now=risk_level(prior_types) if prior else None,
        level_if_posted=risk_level(all_types),
        added=[t for t in TYPE_ORDER if t in new_types and t not in prior_types],
        warnings=warnings,
        regions=regions,
        caption_suggestion=suggestion,
        caption_edits=edits,
        image_size=list(image_size),
        requires_review=result.requires_review,
        review_reasons=result.review_reasons,
    )


def caption_edits(result: AnalyzeResult, caption: str) -> list[CaptionEdit]:
    """캡션 속 단서를 '빼기' 조각으로 나눈다. 사진 속 단서가 캡션에도 그대로 있으면 함께 뺀다."""
    found: list[tuple[str, str]] = []
    for e in result.entities:
        if not e.value:
            continue
        if e.type == "time" and e.evidence == "caption":
            m = TIME_RE.search(caption)
            if m:
                end = m.end()
                if caption[end:end + 1] == "에":  # "8시 40분에" 처럼 조사까지
                    end += 1
                found.append((e.type, caption[m.start():end].strip()))
            continue
        for cand in (f"#{e.value}이", f"#{e.value}", e.value):
            if cand in caption:
                found.append((e.type, cand))
                break
    out: list[CaptionEdit] = []
    for t, text in dict.fromkeys(found):
        if any(text in o.text for o in out):  # 이미 더 긴 조각에 들어 있음
            continue
        out.append(CaptionEdit(id=f"c{len(out) + 1}", type=t, text=text))
    return out


def apply_edits(caption: str, texts: list[str]) -> str:
    for t in sorted(texts, key=len, reverse=True):
        caption = caption.replace(t, " ")
    return re.sub(r"\s+", " ", caption).strip()
