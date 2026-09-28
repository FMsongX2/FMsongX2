# 공개·비공개와 포크를 포함한 소유 저장소의 언어 바이트를 조회해 하나비 원형 게이지를 갱신함.
# 카드 배경과 경기천년체는 저장소 에셋에서 읽고 변경 시 README 이미지 주소도 갱신함.
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "hanabi-github-languages-night.png"
README = ROOT / "README.md"
FONT_DIR = ASSETS / "fonts"
S = 2
W, H = 860, 340
SIZE = (W * S, H * S)
COLORS = ["#FD7688", "#FF9EB3", "#E8365D", "#C9BCD5", "#9DBBE7", "#D39ABB", "#76A4D5", "#FF5E7E"]
KNOWN_COLORS = dict(zip(("TypeScript", "Rust", "Dart", "Shell", "JavaScript", "CSS", "Python", "C++"), COLORS))


def github_json(url: str, token: str) -> object:
    """입력: GitHub API URL·토큰; 반환: 접근 권한이 있는 API의 JSON 응답."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "hanabi-profile-language-card"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.load(response)


def language_bytes(login: str) -> dict[str, int]:
    """입력: GitHub 계정명; 반환: 공개·비공개 소유 저장소 언어 바이트의 합계."""
    private_token = os.environ.get("PROFILE_LANGUAGES_TOKEN")
    if not private_token:
        raise RuntimeError("PROFILE_LANGUAGES_TOKEN is required to avoid a public-only refresh")
    totals: Counter[str] = Counter()
    for private in (False, True):
        token = private_token if private else os.environ.get("GITHUB_TOKEN", "")
        endpoint = ("https://api.github.com/user/repos" if private
                    else f"https://api.github.com/users/{login}/repos")
        page = 1
        while True:
            query = urlencode({"visibility": "private", "affiliation": "owner", "per_page": 100, "page": page} if private
                              else {"type": "owner", "per_page": 100, "page": page})
            repos = github_json(f"{endpoint}?{query}", token)
            if not isinstance(repos, list):
                raise ValueError("GitHub repository response is not a list")
            for repo in repos:
                if repo["private"] != private or repo["owner"]["login"].casefold() != login.casefold():
                    continue
                counts = github_json(repo["languages_url"], token)
                for language, size in counts.items():
                    totals[language] += size
            if len(repos) < 100:
                break
            page += 1
    if not totals:
        raise ValueError("No language data; keeping the existing card")
    return dict(totals)


def fitted_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
    """입력: 그리기 도구·문구·최대 폭·기본 크기; 반환: 카드 폭에 맞는 경기천년체."""
    for size in range(start_size, 11, -1):
        font = ImageFont.truetype(FONT_DIR / "GyeonggiTitle-Medium.ttf", size * S)
        if draw.textlength(text, font=font) <= max_width * S:
            return font
    return font


def render(counts: dict[str, int]) -> bytes:
    """입력: 언어별 바이트 수; 반환: 원형 게이지 PNG 바이트."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("Language byte total must be positive")
    languages = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    image = Image.open(ASSETS / "hanabi-github-languages-bg.png").convert("RGBA")
    if image.size != SIZE:
        raise ValueError(f"Background size must be {SIZE}")
    bold = ImageFont.truetype(FONT_DIR / "GyeonggiTitle-Bold.ttf", 34 * S)
    medium = ImageFont.truetype(FONT_DIR / "GyeonggiTitle-Medium.ttf", 21 * S)

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2*S, 2*S, (W-2)*S, (H-2)*S), radius=20*S, outline="#FD7688", width=2*S)
    cx, cy, radius = 185*S, 170*S, 122*S
    glow = Image.new("RGBA", SIZE)
    ImageDraw.Draw(glow).ellipse((cx-140*S, cy-140*S, cx+140*S, cy+140*S), fill=(253, 118, 136, 50))
    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(24*S)))
    draw = ImageDraw.Draw(image)
    box = (cx-radius, cy-radius, cx+radius, cy+radius)
    draw.arc(box, -90, 270, fill="#47394E", width=36*S)
    angle = -90.0
    for index, (language, size) in enumerate(languages):
        span = size / total * 360
        gap = min(0.12, span / 4)
        draw.arc(box, angle + gap, angle + span - gap,
                 fill=KNOWN_COLORS.get(language, COLORS[index]), width=36*S)
        angle += span

    draw.ellipse((cx-82*S, cy-82*S, cx+82*S, cy+82*S), fill="#211D2C", outline="#6E536C", width=2*S)
    draw.text((380*S, 38*S), "Most Used Languages", font=bold, fill="#FFF5F8")
    for x in range(380*S, 811*S):
        t = (x-380*S) / (430*S)
        color = (round(253*(1-t)+118*t), round(118*(1-t)+94*t), round(136*(1-t)+152*t))
        draw.line((x, 85*S, x, 89*S), fill=color)
    for index, (language, size) in enumerate(languages):
        column, row = divmod(index, 4)
        x = (380 if column == 0 else 610) * S
        y = (114 + row*50) * S
        color = KNOWN_COLORS.get(language, COLORS[index])
        draw.ellipse((x, y+6*S, x+14*S, y+20*S), fill=color)
        label_font = fitted_font(draw, language, 128, 21)
        draw.text((x+25*S, y), language, font=label_font, fill="#F8F0F5")
        draw.text((x+205*S, y), f"{size / total * 100:.2f}%", font=medium, fill="#E7DDEC", anchor="ra")
    clip = Image.new("L", SIZE)
    ImageDraw.Draw(clip).rounded_rectangle((2*S, 2*S, (W-2)*S, (H-2)*S), radius=20*S, fill=255)
    image.putalpha(clip)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def animate(png: bytes) -> bytes:
    """입력: 정적 언어 카드 PNG; 반환: 도넛 중심에 수면 이모티콘을 합성한 GIF."""
    base = Image.open(io.BytesIO(png)).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    emoji_source = Image.open(ASSETS / "hanabi-sleep-transparent.gif")
    palette = base.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    frames = []
    for index in range(140):
        emoji_source.seek(round(index * emoji_source.n_frames / 140))
        emoji = emoji_source.convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)
        frame = base.copy()
        frame.alpha_composite(emoji, (115, 100))
        quantized = frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        result = Image.frombytes("P", frame.size, bytes(value + 1 for value in quantized.tobytes()))
        result.putpalette([0, 0, 0] + quantized.getpalette()[:255 * 3])
        transparent = frame.getchannel("A").point(lambda alpha: 255 if alpha < 128 else 0)
        result.paste(0, mask=transparent)
        result.info["transparency"] = 0
        frames.append(result)
    buffer = io.BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=100,
                   loop=0, disposal=1, optimize=True, transparency=0)
    return buffer.getvalue()


def main() -> None:
    """입력: 선택적 언어 스냅샷 경로; 반환: 없음. 카드와 README 캐시 키를 변경 시 갱신함."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    login = os.environ.get("GITHUB_REPOSITORY_OWNER", "FMsongX2")
    counts = json.loads(args.snapshot.read_text()) if args.snapshot else language_bytes(login)
    png = render(counts)
    gif = animate(png)
    digest = hashlib.sha256(gif).hexdigest()[:12]
    animated_output = ASSETS / f"hanabi-github-languages-{digest}.gif"
    if not OUTPUT.exists() or OUTPUT.read_bytes() != png:
        OUTPUT.write_bytes(png)
    if not animated_output.exists() or animated_output.read_bytes() != gif:
        animated_output.write_bytes(gif)
    legacy = ASSETS / "hanabi-github-languages-animated.gif"
    if legacy.exists():
        legacy.unlink()
    for stale in ASSETS.glob("hanabi-github-languages-????????????.gif"):
        if stale != animated_output and re.fullmatch(r"hanabi-github-languages-[0-9a-f]{12}\.gif", stale.name):
            stale.unlink()
    readme = README.read_text()
    pattern = re.compile(r"hanabi-github-languages-(?:animated|[0-9a-f]{12})\.gif(?:\?v=[0-9a-f]{12})?")
    if not pattern.search(readme):
        raise ValueError("README image reference is missing")
    updated = pattern.sub(animated_output.name, readme)
    if updated != readme:
        README.write_text(updated)
    print(f"{login}: {len(counts)} languages, card revision {digest}")


if __name__ == "__main__":
    main()
