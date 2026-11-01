"""Fast, deterministic caption candidates used alongside GPU image analysis."""
import hashlib
import re

from app.schemas.contracts import Entity

TIME_RE = re.compile(r"(\d{1,2})\s*(?:시|:)\s*(\d{1,2})?\s*분?")
AGE_RE = re.compile(r"(\d{1,2})\s*(살|세)")
SCHOOL_RE = re.compile(r"#?([가-힣A-Za-z0-9]{1,30}(?:초등학교|중학교|고등학교|초교|유치원|어린이집|태권도(?:학원|장)?|학원))")
CLASS_RE = re.compile(r"#?((?:\d{1,2}\s*학년\s*)?\d{1,2}\s*반|[가-힣]+반)(?![가-힣])")
AREA_RE = re.compile(r"#([가-힣]+(?:동|로|길|구|시))(?![가-힣])")
NAME_TAG_RE = re.compile(r"#([가-힣]{1,3})이(?![가-힣])")
NAME_HASH_RE = re.compile(r"#([가-힣]{2,4})(?![가-힣])")
HASHTAG_RE = re.compile(r"#([\w가-힣]+)")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?82[- .]?)?(?:0\d{1,2})[- .]?\d{3,4}[- .]?\d{4}(?!\d)")
EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
SCHEDULE_WORDS = ("등원", "하원", "등교", "하교")


def keyword_hints(caption: str) -> list[str]:
    hints = []
    if SCHOOL_RE.search(caption):
        hints.append("학교·소속")
    if CLASS_RE.search(caption):
        hints.append("반 이름")
    if any(w in caption for w in SCHEDULE_WORDS):
        hints.append("등·하원")
    if TIME_RE.search(caption):
        hints.append("시간")
    if AGE_RE.search(caption):
        hints.append("나이")
    if AREA_RE.search(caption):
        hints.append("동네")
    if NAME_TAG_RE.search(caption):
        hints.append("이름")
    if PHONE_RE.search(caption) or EMAIL_RE.search(caption):
        hints.append("연락처")
    if "생일" in caption:
        hints.append("생일")
    return hints


def caption_entities(caption: str) -> list[Entity]:
    """Extract obvious caption clues locally; final risk level is still rule-based."""
    out: list[Entity] = []
    m = TIME_RE.search(caption)
    if m and any(w in caption for w in SCHEDULE_WORDS):
        out.append(Entity(type="time", value=f"{int(m.group(1))}:{int(m.group(2) or 0):02d}", evidence="caption", why="등·하원 시간 표현"))
    if m := AGE_RE.search(caption):
        out.append(Entity(type="age", value=m.group(0), evidence="caption", why="나이 표현"))
    for m in SCHOOL_RE.finditer(caption):
        out.append(Entity(type="school", value=m.group(1), evidence="caption", why="유치원 이름"))
    for m in CLASS_RE.finditer(caption):
        out.append(Entity(type="school", value=m.group(1), evidence="caption", why="반 이름"))
    for m in AREA_RE.finditer(caption):
        out.append(Entity(type="area", value=m.group(1), evidence="caption", why="동네 해시태그"))
    for m in NAME_TAG_RE.finditer(caption):
        out.append(Entity(type="name", value=m.group(1), evidence="caption", why="이름 해시태그"))
    tagged_names = {e.value.casefold() for e in out if e.type == "name"}
    non_name_values = {
        e.value.casefold() for e in out if e.type in {"age", "area", "contact", "school", "time"}
    }
    stop_names = {"오늘", "우리", "아이", "가족", "엄마", "아빠", "친구", "일상", "행복", "육아", "사랑"}
    for m in NAME_HASH_RE.finditer(caption):
        value = m.group(1)
        normalized = value.casefold()
        # A short hashtag like #망원동 is a location, not a person's name.
        # NAME_TAG_RE already extracts the name without the Korean subject suffix
        # (e.g. #하늘이 -> 하늘), so do not add the whole hashtag as a duplicate.
        duplicates_tagged_name = any(
            normalized == name or normalized == f"{name}이" or name == f"{normalized}이"
            for name in tagged_names
        )
        if normalized not in non_name_values and not duplicates_tagged_name and value not in stop_names:
            out.append(Entity(type="name", value=value, evidence="caption", why="이름일 수 있는 해시태그"))
    for pattern, label in ((PHONE_RE, "전화번호"), (EMAIL_RE, "이메일")):
        for m in pattern.finditer(caption):
            out.append(Entity(type="contact", value=m.group(0), evidence="caption", why=label))
    return out


def caption_candidates(caption: str, post_id: str) -> list[dict]:
    """CPU-only first-pass clue list; uncertain hashtags remain user-editable candidates."""
    candidates = []
    seen = set()
    hashtags = {value for value in HASHTAG_RE.findall(caption)}
    for entity in caption_entities(caption):
        key = (entity.type, entity.value.casefold())
        if key in seen:
            continue
        seen.add(key)
        source = "hashtag" if entity.value in hashtags else "caption"
        digest = hashlib.sha256(f"{post_id}\0{entity.type}\0{entity.value.casefold()}\0{source}".encode("utf-8")).hexdigest()[:12]
        candidates.append({
            "id": f"{post_id}:{digest}", "type": entity.type, "value": entity.value,
            "source": source, "why": entity.why, "selected_by_default": True,
        })
    return candidates


def extract_hashtags(caption: str) -> list[str]:
    return list(dict.fromkeys(HASHTAG_RE.findall(caption)))
