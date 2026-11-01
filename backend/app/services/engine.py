"""백엔드 분석 로직: 게시물별 단서를 이어 위험 단계를 표기하고 최소 정리를 계산한다 (직접 개발)."""
from collections import Counter
from itertools import combinations
from typing import Optional

from app.schemas.contracts import (
    LEVEL_ORDER,
    CleanupItem,
    Clue,
    EngineResult,
    Entity,
    Level,
    risk_level,
)

TYPE_LABEL = {"name": "이름", "age": "나이", "school": "학교·소속", "area": "장소", "time": "시간·일정", "contact": "연락처"}
TYPE_ORDER = ["name", "age", "school", "area", "time", "contact"]
MAX_CLEANUP = 5  # 최소 정리로 추천할 게시물 수 상한


def level_rank(level: Level) -> int:
    return LEVEL_ORDER.index(level)


def reason_types(types: set[str]) -> list[str]:
    """위험 단계를 만든 단서 조합 (표의 조건에 해당하는 것만)."""
    level = risk_level(types)
    if level == "very_high":
        place = [t for t in ("school", "area") if t in types]
        return ["name", *place, "time"]
    if level == "high":
        return ["name", *[t for t in ("school", "area") if t in types]]
    return [t for t in TYPE_ORDER if t in types]


def explain(reason: list[str], level: Level) -> str:
    if level == "safe":
        return "아이를 특정할 단서가 없어요."
    joined = " + ".join(TYPE_LABEL[t] for t in reason)
    tail = {
        "caution": "이 보이지만, 어디서 만날 수 있는지는 드러나지 않아요.",
        "high": "이 이어져서, 그 장소에서 이름을 부르며 다가갈 수 있어요.",
        "very_high": "이 이어져서, 언제 어디서 아이를 만날 수 있는지 드러나요.",
    }[level]
    return f"{joined}{tail}"


def _types_of(post_entities: dict[str, list[Entity]], exclude: set[str] = frozenset()) -> set[str]:
    return {e.type for pid, ents in post_entities.items() if pid not in exclude for e in ents}


def _cuts(post_types: set[str], before_reason: list[str], after: set[str]) -> list[str]:
    """이 게시물을 정리하면 끊기는 연결 (예: 이름 ↔ 유치원)."""
    out = []
    for lost in (t for t in before_reason if t in post_types and t not in after):
        partner = next((r for r in before_reason if r != lost and r in after), None) or next(
            (r for r in before_reason if r != lost), None
        )
        if not partner:
            out.append(TYPE_LABEL[lost])
            continue
        a, b = sorted((partner, lost), key=TYPE_ORDER.index)
        out.append(f"{TYPE_LABEL[a]} ↔ {TYPE_LABEL[b]}")
    return list(dict.fromkeys(out))


def minimal_cleanup(post_entities: dict[str, list[Entity]]) -> tuple[list[str], Optional[Level]]:
    """'주의' 이하로 내려가는 가장 적은 게시물 조합. 같은 개수면 단계가 더 낮아지는 쪽."""
    current = risk_level(_types_of(post_entities))
    if level_rank(current) <= level_rank("caution"):
        return [], None
    candidates = [pid for pid, ents in post_entities.items() if ents]
    best: tuple[int, list[str]] | None = None
    for k in range(1, min(MAX_CLEANUP, len(candidates)) + 1):
        for combo in combinations(candidates, k):
            lvl = risk_level(_types_of(post_entities, set(combo)))
            if level_rank(lvl) <= level_rank("caution") and (best is None or level_rank(lvl) < best[0]):
                best = (level_rank(lvl), list(combo))
        if best:
            break
    if not best:
        return [], None
    return best[1], LEVEL_ORDER[best[0]]


def most_common_value(entities: list[Entity], t: str) -> str:
    values = [e.value for e in entities if e.type == t]
    return Counter(values).most_common(1)[0][0] if values else ""


def build_result(
    post_entities: dict[str, list[Entity]],
    post_meta: dict[str, dict],
    failed_photo_ids: list[str],
) -> EngineResult:
    all_entities = [e for ents in post_entities.values() for e in ents]
    types = {e.type for e in all_entities}
    level = risk_level(types)
    reason = reason_types(types)
    card = {t: most_common_value(all_entities, t) for t in TYPE_ORDER if t in types}
    sources = {t: [pid for pid, ents in post_entities.items() if any(e.type == t for e in ents)] for t in card}
    cleanup, after = minimal_cleanup(post_entities)
    remaining = sorted(_types_of(post_entities, set(cleanup)), key=TYPE_ORDER.index) if cleanup else []

    items = []
    after_types = _types_of(post_entities, set(cleanup))
    for pid in cleanup:
        ents = post_entities[pid]
        items.append(
            CleanupItem(
                post_id=pid,
                posted_at=post_meta.get(pid, {}).get("posted_at"),
                caption=post_meta.get(pid, {}).get("caption", "")[:80],
                photo_ids=post_meta.get(pid, {}).get("photo_ids", []),
                clues=list({(e.type, e.value): Clue(type=e.type, value=e.value) for e in ents}.values()),
                cuts=_cuts({e.type for e in ents}, reason, after_types),
            )
        )

    clues = [Clue(type=t, value=card[t]) for t in card]
    return EngineResult(
        level=level,
        reason=reason,
        card=card,
        sources=sources,
        explanation=explain(reason, level),
        cleanup=cleanup,
        cleanup_items=items,
        level_after_cleanup=after,
        remaining_after_cleanup=remaining,
        clues=clues,
        analyzed_posts=len(post_entities),
        failed_photo_ids=failed_photo_ids,
    )


def dedupe(entities: list[Entity]) -> list[Entity]:
    seen, out = set(), []
    for e in entities:
        key = (e.type, e.value.strip(), e.evidence, tuple(e.box or []))
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out
