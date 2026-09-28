# 3D 기여 그래프에서 언어 도넛·활동 레이더·하단 수치를 제거함.
# 기여 평면은 원본 생성 결과를 유지함.
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def main(path: Path) -> None:
    """입력: 생성된 SVG 경로; 반환: 없음. 기여 평면 외 통계 그룹을 제거해 저장함."""
    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)
    tree = ET.parse(path)
    root = tree.getroot()
    groups = [element for element in root if element.tag == f"{{{namespace}}}g"]
    for element in groups:
        if element.get("transform") == "translate(40, 520)" or any(
            node.text in {"Commit", "contributions"} for node in element.iter()
        ):
            root.remove(element)
    tree.write(path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
