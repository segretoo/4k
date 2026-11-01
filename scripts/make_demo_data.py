"""시연용 가상 계정 데이터 생성 (합성 이미지, 실제 아이 사진 없음).

인스타그램 '내 정보 내보내기'와 같은 구조의 zip과, 가짜 GPU가 쓰는 정답표를 만든다.
  python scripts/make_demo_data.py            # data/demo/ 에 생성
  python scripts/make_demo_data.py --font C:/Windows/Fonts/malgun.ttf

화면 속 이름·유치원·동네·시간은 모두 가상 값이다.
"""
import argparse
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "demo"
KST = timezone(timedelta(hours=9))
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "C:/Windows/Fonts/malgunbd.ttf",
    "C:/Windows/Fonts/malgun.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]

# (날짜, 캡션, 장면, [(글자, 종류, 판넬)]) — 최신순 아님, 아래에서 정렬
POSTS = [
    ("2026-03-04 08:10", "첫 등원! 떨렸지만 씩씩하게 🎒 #햇살유치원 #하늘이", "school_gate", [("햇살유치원", "school", "board"), ("하늘", "name", "tag")]),
    ("2026-04-12 15:20", "꽃구경 🌸", "flowers", []),
    ("2026-05-02 10:05", "소풍 날 🍙 #해바라기반", "picnic", [("햇살유치원", "school", "logo")]),
    ("2026-06-02 17:40", "놀이터에서 신났다", "playground", []),
    ("2026-07-10 19:00", "새 가방 생겼어요 🎒", "bag", [("하늘", "name", "tag")]),
    ("2026-08-20 12:30", "바다 여행 🌊", "sea", []),
    ("2026-09-03 08:45", "등원길 산책 🚶 8시 40분 #개포동", "street", [("개포로", "area", "road")]),
    ("2026-09-15 11:00", "카페 라떼 ☕", "coffee", []),
    ("2026-09-28 18:30", "#하늘이 5살 생일 축하해 🎂", "cake", [("하늘", "name", "cake")]),
    ("2026-10-05 13:10", "주말 브런치 🥞", "food", []),
    ("2026-10-12 09:30", "가을 소풍 🍂 #햇살유치원", "autumn", []),
    ("2026-10-20 19:20", "집밥 🍲", "food2", []),
]

SCENE_BG = {
    "school_gate": ("#FFE3D3", "#CDEBD9"), "flowers": ("#FDE7F0", "#D9EED2"), "picnic": ("#E3F1FB", "#CDEBD9"),
    "playground": ("#E9E4FA", "#F3E2C4"), "bag": ("#FFF1DA", "#EADBC8"), "sea": ("#D9EEFA", "#A9D3EE"),
    "street": ("#EDEFF2", "#C9CCD2"), "coffee": ("#F3E6DA", "#D8C2AE"), "cake": ("#FFE7EA", "#F6D2D8"),
    "food": ("#FFF5E1", "#F0DDBD"), "autumn": ("#FCE9D6", "#E9C9A0"), "food2": ("#F6EFE6", "#E1D3C1"),
}


def font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    for p in [path, *FONT_CANDIDATES]:
        if p and Path(p).exists():
            return ImageFont.truetype(p, size)
    raise SystemExit("한글 글꼴을 찾지 못했어요. --font 로 경로를 지정해 주세요.")


def draw_scene(scene: str, panels: list, font_path: str | None) -> tuple[Image.Image, list[dict]]:
    W = H = 1080
    sky, ground = SCENE_BG[scene]
    im = Image.new("RGB", (W, H), sky)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 760, W, H), fill=ground)
    d.ellipse((820, 90, 960, 230), fill="#FFD36E")  # 해
    if scene.startswith("food") or scene in {"coffee", "cake"}:
        d.ellipse((290, 380, 790, 880), fill="#FFFFFF", outline="#E2D6CC", width=10)
        d.ellipse((400, 490, 680, 770), fill="#E8A87C" if scene != "coffee" else "#B08968")
    else:  # 사람 대신 얼굴 없는 실루엣
        d.rounded_rectangle((470, 420, 610, 760), radius=60, fill="#9AA0C0")
        d.ellipse((480, 320, 600, 440), fill="#F2C8A8")
    boxes = []
    for text, typ, kind in panels:
        size = {"tag": 64, "board": 84, "logo": 52, "road": 72, "cake": 70}[kind]
        f = font(font_path, size)
        tw, th = d.textbbox((0, 0), text, font=f)[2:]
        if kind == "board":
            x, y = 140, 120
            d.rectangle((x - 30, y - 24, x + tw + 30, y + th + 30), fill="#FFE07A", outline="#8A5A2B", width=8)
            fill = "#5B3A29"
        elif kind == "road":
            x, y = 120, 200
            d.rounded_rectangle((x - 30, y - 24, x + tw + 30, y + th + 34), radius=14, fill="#1F6E43", outline="#FFFFFF", width=6)
            fill = "#FFFFFF"
        elif kind == "tag":
            x, y = 640, 560
            d.rounded_rectangle((x - 20, y - 16, x + tw + 20, y + th + 24), radius=12, fill="#FFFFFF", outline="#C8483E", width=6)
            fill = "#3B2420"
        elif kind == "logo":
            x, y = 470, 600
            d.rectangle((x - 14, y - 10, x + tw + 14, y + th + 18), fill="#F6C945")
            fill = "#3B2420"
        else:  # cake
            x, y = 540 - tw // 2, 580
            fill = "#C8483E"
        d.text((x, y), text, font=f, fill=fill)
        bx = d.textbbox((x, y), text, font=f)
        boxes.append({"text": text, "type": typ, "box": [int(v) for v in bx]})
    small = font(font_path, 26)
    d.text((24, H - 48), "합성 이미지 · SAMPLE · 가상 값", font=small, fill="#7A5048")
    return im, boxes


def meta_encode(s: str) -> str:
    """Meta 내보내기처럼 UTF-8을 latin-1로 한 번 더 감싼다 (백엔드의 깨짐 복원 테스트용)."""
    return s.encode("utf-8").decode("latin-1")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--font")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    posts_json, fixture, truth = [], {}, []
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, (when, caption, scene, panels) in enumerate(POSTS, start=1):
            dt = datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            ts = int(dt.timestamp())
            im, boxes = draw_scene(scene, panels, args.font)
            name = f"demo_{i:02d}_{scene}.jpg"
            uri = f"media/posts/{dt:%Y%m}/{name}"
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=90)
            z.writestr(uri, buf.getvalue())
            media = [{"uri": uri, "creation_timestamp": ts, "title": ""}]
            if scene == "sea":  # 동영상은 백엔드가 건너뛰는지 확인용
                z.writestr(f"media/posts/{dt:%Y%m}/demo_{i:02d}_clip.mp4", b"\x00\x00\x00\x18ftypmp42")
                media.append({"uri": f"media/posts/{dt:%Y%m}/demo_{i:02d}_clip.mp4", "creation_timestamp": ts, "title": ""})
            posts_json.append({"media": media, "title": meta_encode(caption), "creation_timestamp": ts})
            fixture[name] = {
                "texts": [{"text": b["text"], "box": b["box"], "source": "vlm", "conf": 0.93} for b in boxes],
                "entities": [
                    {"type": b["type"], "value": b["text"], "evidence": "image", "box": b["box"], "why": "사진 속 글자"}
                    for b in boxes
                ],
            }
            truth.append({"file": name, "caption": caption, "image_clues": [{"type": b["type"], "value": b["text"]} for b in boxes]})
        z.writestr("your_instagram_activity/media/posts_1.json", json.dumps(posts_json, ensure_ascii=True))
        # '미디어'만 체크하지 않았을 때 섞여 들어오는 파일: 백엔드가 열지 않아야 함
        z.writestr("connections/followers_and_following/followers_1.json", json.dumps([{"string_list_data": [{"value": "demo_friend"}]}]))
        z.writestr("personal_information/personal_information/personal_information.json", json.dumps({"profile_user": []}))

    # UC2 시연용 사진 한 장 (이름표 + 캡션의 등원 시간)
    im, boxes = draw_scene("bag", [("하늘", "name", "tag")], args.font)
    im.save(OUT / "uc2_demo.jpg", "JPEG", quality=90)
    fixture["uc2_demo.jpg"] = {
        "texts": [{"text": b["text"], "box": b["box"], "source": "vlm", "conf": 0.93} for b in boxes],
        "entities": [{"type": b["type"], "value": b["text"], "evidence": "image", "box": b["box"], "why": "사진 속 글자"} for b in boxes],
    }

    (OUT / "instagram-demo.zip").write_bytes(zbuf.getvalue())
    (OUT / "mock_gpu.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "answer_key.json").write_text(json.dumps(truth, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"생성 완료: {OUT}")


if __name__ == "__main__":
    main()
