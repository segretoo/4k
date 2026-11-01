"""점검할 사진 추천: 캡션 글자만 GPU(Qwen)로 보내 점수를 받고, 단서가 있는 게시물 → 최근순으로 채운다."""
from app.config import settings
from app.schemas.contracts import CaptionCandidate, PhotoSummary, PostSummary, ScreenResult
from app.services.text_rules import caption_candidates, extract_hashtags, keyword_hints


async def screen(posts: list[dict], owner_id: str = "") -> dict[str, ScreenResult]:
    """Cheap CPU-only candidate pass; full OCR/VLM is deferred until user confirms photos."""
    results: dict[str, ScreenResult] = {}
    for p in posts:
        hints = keyword_hints(p.get("caption", ""))
        clues = caption_candidates(p.get("caption", ""), p["post_id"])
        # Score only orders the review list; it does not make a safety decision.
        score = min(1.0, 0.2 * len(clues) + 0.1 * len(hints))
        p["hashtags"] = p.get("hashtags") or extract_hashtags(p.get("caption", ""))
        p["candidates"] = clues
        results[p["post_id"]] = ScreenResult(post_id=p["post_id"], score=score, hints=hints)
    return results


def pick(posts: list[dict], scores: dict[str, ScreenResult]) -> list[str]:
    """단서 점수가 있는 게시물(점수순) → 나머지 최근순. posts는 이미 최근순."""
    order = sorted(posts, key=lambda p: -scores[p["post_id"]].score) if posts else []
    picked: list[str] = []
    for p in order:
        if scores[p["post_id"]].score <= 0:
            break
        for ph in p["photos"]:
            if len(picked) < settings.max_photos:
                picked.append(ph["photo_id"])
    for p in posts:
        for ph in p["photos"]:
            if len(picked) >= settings.max_photos:
                return picked
            if ph["photo_id"] not in picked:
                picked.append(ph["photo_id"])
    return picked


def summaries(upload_id: str, posts: list[dict], scores: dict[str, ScreenResult], picked: list[str]) -> list[PostSummary]:
    out = []
    for p in posts:
        s = scores[p["post_id"]]
        out.append(
            PostSummary(
                post_id=p["post_id"],
                posted_at=p["posted_at"],
                caption=p["caption"],
                hashtags=p.get("hashtags", extract_hashtags(p.get("caption", ""))),
                candidates=[CaptionCandidate(**c) for c in p.get("candidates", [])],
                photos=[
                    PhotoSummary(photo_id=ph["photo_id"], thumb_url=f"/api/uc1/uploads/{upload_id}/thumbs/{ph['photo_id']}")
                    for ph in p["photos"]
                ],
                recommended=any(ph["photo_id"] in picked for ph in p["photos"]) and s.score > 0,
                hints=s.hints,
                score=s.score,
            )
        )
    return out
