# 생성된 3D 기여 그래프의 빈 모서리에 두 하나비 애니메이션을 합성함.
# SVG와 애니메이션의 갱신 책임은 기존 워크플로와 assets에 유지함.
import base64
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def main(graph: Path, left: Path, right: Path, output: Path) -> None:
    """입력: 잔디 SVG·양쪽 APNG·출력 경로; 반환: 없음. 재생 가능한 합성 SVG를 저장함."""
    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)
    tree = ET.parse(graph)
    root = tree.getroot()
    for path, x, y, size, aspect in (
        (left, 0, 470, 380, "xMidYMax slice"),
        (right, 900, 40, 380, "xMidYMid meet"),
    ):
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        ET.SubElement(root, f"{{{namespace}}}image", {
            "x": str(x), "y": str(y), "width": str(size), "height": str(size),
            "preserveAspectRatio": aspect,
            "href": f"data:image/png;base64,{encoded}",
        })
    tree.write(output, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main(*(Path(argument) for argument in sys.argv[1:]))
