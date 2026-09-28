# 언어 API 집계의 저장소 필터와 원형 카드의 출력 계약을 확인함.
# 외부 네트워크 없이 실행하며 실제 API 연결은 갱신 작업에서 확인함.
import io

from PIL import Image

import update_languages as card


def fake_github_json(url: str) -> object:
    """입력: 테스트 API URL; 반환: 원본·포크·타인 저장소를 섞은 응답."""
    if "/users/" in url:
        return [
            {"fork": False, "private": False, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/one"},
            {"fork": False, "private": False, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/two"},
            {"fork": True, "private": False, "owner": {"login": "FMsongX2"}, "languages_url": "https://example.test/fork"},
            {"fork": False, "private": False, "owner": {"login": "other"}, "languages_url": "https://example.test/other"},
        ]
    return {"https://example.test/one": {"TypeScript": 100}, "https://example.test/two": {"TypeScript": 50, "Rust": 50}}[url]


card.github_json = fake_github_json
counts = card.language_bytes("FMsongX2")
assert counts == {"TypeScript": 150, "Rust": 50}
png = card.render(counts)
assert png == card.render(counts)
image = Image.open(io.BytesIO(png)).convert("RGBA")
assert image.size == card.SIZE
assert image.getpixel((0, 0))[3] == 0
assert image.getpixel((card.W, card.H))[3] == 255
print("language aggregation and chart rendering OK")
