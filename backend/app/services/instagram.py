"""인스타그램 내보내기 ZIP에서 게시물 메타데이터와 연결된 사진만 읽는다."""
import io
import json
import posixpath
import re
import zipfile
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.services.text_rules import extract_hashtags

POSTS_JSON_RE = re.compile(r"(^|/)posts_\d+\.json$")
POSTS_HTML_RE = re.compile(r"(^|/)posts_\d+\.html$", re.IGNORECASE)
POSTS_INDEX_HTML_RE = re.compile(r"(^|/)posts\.html$", re.IGNORECASE)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
KST = timezone(timedelta(hours=9))
HANGUL_RE = re.compile(r"[가-힣]")


class ExportError(ValueError):
    """사용자에게 보여 줄 수 있는 오류."""


def fix_mojibake(text: str) -> str:
    """Meta 내보내기 JSON은 UTF-8을 latin-1로 한 번 더 감싸는 경우가 많다."""
    if not text:
        return ""
    try:
        fixed = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return fixed if HANGUL_RE.search(fixed) or fixed != text else text


def _safe_name(name: str) -> bool:
    p = PurePosixPath(name)
    return not (p.is_absolute() or ".." in p.parts or name.startswith("\\"))


def _check_zip(zf: zipfile.ZipFile) -> None:
    infos = zf.infolist()
    if len(infos) > settings.max_zip_files:
        raise ExportError("압축 파일 안의 파일이 너무 많아요.")
    total = sum(i.file_size for i in infos)
    if total > settings.max_unzipped_mb * 1024 * 1024:
        raise ExportError("압축을 풀었을 때 크기가 너무 커요. 기간을 줄여서 다시 내보내 주세요.")
    for i in infos:
        if not _safe_name(i.filename):
            raise ExportError("압축 파일 안에 올바르지 않은 경로가 있어요.")


def _find_posts_json(zf: zipfile.ZipFile) -> list[str]:
    names = [n for n in zf.namelist() if POSTS_JSON_RE.search(n)]
    return sorted(names)


def _natural_part_number(path: str) -> int:
    match = re.search(r"posts_(\d+)\.html$", path, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _find_posts_html(zf: zipfile.ZipFile) -> list[str]:
    names = zf.namelist()
    numbered = sorted((n for n in names if POSTS_HTML_RE.search(n)), key=lambda n: (_natural_part_number(n), n))
    if numbered:
        return numbered
    return sorted(n for n in names if POSTS_INDEX_HTML_RE.search(n))


class _PostHTMLParser(HTMLParser):
    """Read post cards from Meta's newer HTML export without retaining page markup."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.posts: list[dict] = []
        self.current: dict | None = None
        self.div_depth = 0
        self.in_caption = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if self.current is None and tag == "div":
            classes = set((attrs.get("class") or "").split())
            if {"pam", "_a6-g", "uiBoxWhite"}.issubset(classes):
                self.current = {"caption_parts": [], "uris": [], "posted_at": None, "has_post_heading": False}
                self.div_depth = 1
                return
        if self.current is None:
            return
        if tag == "div":
            self.div_depth += 1
        elif tag == "h2":
            self.current["has_post_heading"] = True
            self.in_caption = True
        elif tag == "time" and not self.current["posted_at"]:
            self.current["posted_at"] = attrs.get("datetime")
        elif tag == "a":
            self._add_uri(attrs.get("href"))
        elif tag == "img":
            self._add_uri(attrs.get("src"))

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        if tag == "h2":
            self.in_caption = False
        elif tag == "div":
            self.div_depth -= 1
            if self.div_depth == 0:
                caption = "".join(self.current["caption_parts"])
                caption = caption.replace("\u200b", "").replace("\ufeff", "")
                caption = re.sub(r"[ \t\r\n]+", " ", caption).strip()
                uris = list(dict.fromkeys(self.current["uris"]))
                # The full posts.html page also uses _a6-g for nested metadata cells;
                # actual post cards have the h2 heading, even when the caption is empty.
                if self.current["has_post_heading"]:
                    self.posts.append({
                        "title": caption,
                        "creation_timestamp": None,
                        "media": [{"uri": uri} for uri in uris],
                        "html_posted_at": self.current["posted_at"],
                    })
                self.current = None
                self.in_caption = False

    def handle_data(self, data: str) -> None:
        if self.current is not None and self.in_caption:
            self.current["caption_parts"].append(data)

    def _add_uri(self, uri: str | None) -> None:
        if not uri:
            return
        uri = uri.strip()
        if PurePosixPath(uri.split("?", 1)[0]).suffix.lower() in IMAGE_EXT:
            self.current["uris"].append(uri.split("?", 1)[0])


def _parse_posts_html(raw: bytes) -> list[dict]:
    parser = _PostHTMLParser()
    parser.feed(raw.decode("utf-8-sig", errors="replace"))
    parser.close()
    return parser.posts


def _posted_at(ts) -> str | None:
    try:
        return datetime.fromtimestamp(int(ts), tz=KST).isoformat()
    except (TypeError, ValueError, OSError):
        try:
            value = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(KST).isoformat()
        except (TypeError, ValueError, OverflowError):
            return None


def _resolve_member(zf_names: set[str], uri: str, source_path: str) -> str | None:
    """uri는 보통 'media/posts/202603/xxx.jpg'. zip 최상위 폴더 유무가 달라도 찾는다."""
    uri = uri.replace("\\", "/").split("?", 1)[0]
    candidates = [uri.lstrip("/")]
    if uri.startswith("../") or uri.startswith("./"):
        candidates.append(posixpath.normpath(posixpath.join(posixpath.dirname(source_path), uri)))
    for candidate in candidates:
        if candidate in zf_names:
            return candidate
        matches = sorted(n for n in zf_names if n.endswith("/" + candidate))
        if matches:
            return matches[0]
    return None


def _save_photo(raw: bytes, photo_path: Path, thumb_path: Path) -> tuple[int, int] | None:
    """확장자가 아니라 실제 내용으로 이미지인지 확인하고, 방향 보정 + 메타데이터 없는 새 파일로 저장."""
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if max(im.size) > settings.max_image_side:
                im.thumbnail((settings.max_image_side, settings.max_image_side))
            im.save(photo_path, "JPEG", quality=92)
            th = im.copy()
            th.thumbnail((settings.thumb_side, settings.thumb_side))
            th.save(thumb_path, "JPEG", quality=80)
            return im.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return None


def extract(zip_path: Path, dest: Path) -> list[dict]:
    """JSON/HTML 내보내기에서 필요한 사진만 꺼내고 게시물 목록을 저장한다."""
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as e:
        raise ExportError("zip 파일이 아니에요.") from e
    with zf:
        _check_zip(zf)
        json_names = _find_posts_json(zf)
        html_names = [] if json_names else _find_posts_html(zf)
        if not json_names and not html_names:
            raise ExportError("게시물 파일을 찾지 못했어요. Instagram 내보내기 ZIP에 게시물 미디어가 포함되어 있는지 확인해 주세요.")
        names = set(zf.namelist())

        raw_posts = []
        if json_names:
            for jn in json_names:
                try:
                    data = json.loads(zf.read(jn))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    raise ExportError("게시물 JSON을 읽지 못했어요.") from e
                if isinstance(data, dict):  # 일부 내보내기는 {"...": [...]} 형태
                    data = next((v for v in data.values() if isinstance(v, list)), [])
                raw_posts.extend((jn, p) for p in data if isinstance(p, dict))
        else:
            seen_html_posts: set[tuple[str, tuple[str, ...]]] = set()
            for html_path in html_names:
                for post in _parse_posts_html(zf.read(html_path)):
                    image_uris = tuple(m["uri"] for m in post.get("media", []))
                    signature = (post.get("title", "").casefold(), image_uris)
                    if signature in seen_html_posts:
                        continue  # posts.html과 posts_1.html이 같은 게시물 목록인 내보내기 중복 방지
                    seen_html_posts.add(signature)
                    raw_posts.append((html_path, post))

        def ts_of(p: dict) -> int:
            media = p.get("media") or []
            raw = (p.get("creation_timestamp")
                   or (media[0].get("creation_timestamp") if media else None)
                   or p.get("html_posted_at") or 0)
            try:
                return int(raw or 0)
            except (TypeError, ValueError):
                try:
                    value = datetime.fromisoformat(str(p.get("html_posted_at", raw)).replace("Z", "+00:00"))
                    if value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    return int(value.timestamp())
                except (TypeError, ValueError, OverflowError, OSError):
                    return 0

        raw_posts.sort(key=lambda x: ts_of(x[1]), reverse=True)
        raw_posts = raw_posts[: settings.max_candidate_posts]

        posts = []
        for idx, (jn, p) in enumerate(raw_posts, start=1):
            media = p.get("media") or []
            caption = fix_mojibake(p.get("title") or (media[0].get("title") if media else "") or "")
            post_id = f"p{idx:03d}"
            photos = []
            for m_idx, m in enumerate(media, start=1):
                uri = m.get("uri") or ""
                if PurePosixPath(uri).suffix.lower() not in IMAGE_EXT:
                    continue  # 동영상·릴스 제외
                member = _resolve_member(names, uri, jn)
                if not member:
                    continue
                photo_id = f"{post_id}_{m_idx}"
                size = _save_photo(zf.read(member), dest / "photos" / f"{photo_id}.jpg", dest / "thumbs" / f"{photo_id}.jpg")
                if size:
                    photos.append({"photo_id": photo_id, "source": PurePosixPath(uri).name, "size": list(size)})
            if photos:
                posts.append(
                    {
                        "post_id": post_id,
                        "posted_at": _posted_at(p.get("html_posted_at") or ts_of(p)),
                        "caption": caption,
                        "hashtags": extract_hashtags(caption),
                        "photos": photos,
                    }
                )

    zip_path.unlink(missing_ok=True)  # zip은 꺼낸 직후 삭제
    if not posts:
        raise ExportError("점검할 수 있는 사진이 없어요.")
    (dest / "posts.json").write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")
    return posts


def load_posts(dest: Path) -> list[dict]:
    return json.loads((dest / "posts.json").read_text(encoding="utf-8"))


def save_posts(dest: Path, posts: list[dict]) -> None:
    path = dest / "posts.json"
    temp_path = dest / "posts.json.tmp"
    temp_path.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)
