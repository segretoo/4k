"""인스타그램 내보내기 zip 처리: 게시물 JSON과 사진만 꺼내고 나머지는 풀지 않는다."""
import io
import json
import re
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings

POSTS_JSON_RE = re.compile(r"(^|/)posts_\d+\.json$")
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


def _posted_at(ts) -> str | None:
    try:
        return datetime.fromtimestamp(int(ts), tz=KST).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _resolve_member(zf_names: set[str], uri: str, json_path: str) -> str | None:
    """uri는 보통 'media/posts/202603/xxx.jpg'. zip 최상위 폴더 유무가 달라도 찾는다."""
    uri = uri.lstrip("/")
    if uri in zf_names:
        return uri
    for n in zf_names:
        if n.endswith("/" + uri):
            return n
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
    """zip을 검사하고 필요한 파일만 꺼낸다. 반환: 최신순 게시물 목록 (posts.json으로도 저장)."""
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as e:
        raise ExportError("zip 파일이 아니에요.") from e
    with zf:
        _check_zip(zf)
        json_names = _find_posts_json(zf)
        if not json_names:
            raise ExportError("게시물 JSON(posts_1.json)을 찾지 못했어요. '미디어'를 체크하고 JSON 형식으로 내보냈는지 확인해 주세요.")
        names = set(zf.namelist())

        raw_posts = []
        for jn in json_names:
            try:
                data = json.loads(zf.read(jn))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ExportError("게시물 JSON을 읽지 못했어요.") from e
            if isinstance(data, dict):  # 일부 내보내기는 {"...": [...]} 형태
                data = next((v for v in data.values() if isinstance(v, list)), [])
            raw_posts.extend((jn, p) for p in data if isinstance(p, dict))

        def ts_of(p: dict) -> int:
            media = p.get("media") or []
            return int(p.get("creation_timestamp") or (media[0].get("creation_timestamp") if media else 0) or 0)

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
                        "posted_at": _posted_at(ts_of(p)),
                        "caption": caption,
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
