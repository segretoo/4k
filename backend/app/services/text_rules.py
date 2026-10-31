"""캡션 단어 규칙. 추천 순서를 정하는 보조 수단과 가짜 GPU에서만 쓴다.
실제 단서 판단은 GPU 서버의 Qwen 프롬프트가 한다 (멘토링 결정)."""
import re

from app.schemas.contracts import Entity

TIME_RE = re.compile(r"(\d{1,2})\s*(?:시|:)\s*(\d{1,2})?\s*분?")
AGE_RE = re.compile(r"(\d{1,2})\s*(살|세)")
SCHOOL_RE = re.compile(r"#?([가-힣A-Za-z]+(?:유치원|어린이집))")
CLASS_RE = re.compile(r"#([가-힣]+반)(?![가-힣])")
AREA_RE = re.compile(r"#([가-힣]+(?:동|로|길))(?![가-힣])")
NAME_TAG_RE = re.compile(r"#([가-힣]{1,3})이(?![가-힣])")
SCHEDULE_WORDS = ("등원", "하원", "등교", "하교")


def keyword_hints(caption: str) -> list[str]:
    hints = []
    if SCHOOL_RE.search(caption):
        hints.append("유치원")
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
    if "생일" in caption:
        hints.append("생일")
    return hints


def caption_entities(caption: str) -> list[Entity]:
    """가짜 GPU 전용: 캡션에서 단서를 단어 규칙으로 뽑는다."""
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
    return out
