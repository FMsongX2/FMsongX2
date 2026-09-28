# 언어 API 집계에 공개·비공개·포크가 포함되는지와 원형 카드의 출력 계약을 확인함.
# 외부 네트워크 없이 실행하며 실제 API 연결은 갱신 작업에서 확인함.
import io

from PIL import Image

import update_languages as card


def fake_github_json(url: str, token: str) -> object:
    """입력: 테스트 API URL·토큰; 반환: 공개·비공개·포크·타인 저장소를 섞은 응답."""
    assert token == ("private-read" if "/user/repos" in url or "/private" in url else "public-read")
    if "/users/" in url:
        return [
            {"fork": False, "private": False, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/one"},
            {"fork": False, "private": False, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/two"},
            {"fork": True, "private": False, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/fork"},
            {"fork": False, "private": False, "owner": {"login": "other"}, "languages_url": "https://example.test/other"},
        ]
    if "/user/repos" in url:
        return [
            {"fork": False, "private": True, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/private"},
            {"fork": False, "private": True, "owner": {"login": "other"}, "languages_url": "https://example.test/collaborator"},
        ]
    return {"https://example.test/one": {"TypeScript": 100}, "https://example.test/two": {"TypeScript": 50, "Rust": 50}, "https://example.test/fork": {"C#": 30}, "https://example.test/private": {"C#": 70}}[url]


card.github_json = fake_github_json
card.os.environ["GITHUB_TOKEN"] = "public-read"
card.os.environ["PROFILE_LANGUAGES_TOKEN"] = "private-read"
counts = card.language_bytes("FMsongX2")
assert counts == {"TypeScript": 150, "Rust": 50, "C#": 100}
card.os.environ.pop("PROFILE_LANGUAGES_TOKEN")
try:
    card.language_bytes("FMsongX2")
except RuntimeError:
    pass
else:
    raise AssertionError("Missing private token must not refresh public-only data")
png = card.render(counts)
assert png == card.render(counts)
image = Image.open(io.BytesIO(png)).convert("RGBA")
assert image.size == card.SIZE
assert image.getpixel((0, 0))[3] == 0
assert image.getpixel((card.W, card.H))[3] == 255
print("language aggregation and chart rendering OK")
