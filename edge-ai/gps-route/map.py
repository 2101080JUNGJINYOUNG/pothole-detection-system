import os
import zipfile
import xml.etree.ElementTree as ET


def load_kmz_coords(kmz_path: str):
    """
    KMZ 파일 안의 LineString 좌표들을 (lat, lon) 리스트로 반환
    """
    print(f"[DEBUG] load_kmz_coords() called with: {kmz_path}")

    # 1) kmz(zip) 열기
    with zipfile.ZipFile(kmz_path, "r") as z:
        print("[DEBUG] KMZ 열기 성공. 내부 파일 목록:", z.namelist())

        # 안에 들어 있는 .kml 파일 이름 찾기
        kml_name = None
        for name in z.namelist():
            if name.lower().endswith(".kml"):
                kml_name = name
                break
        if kml_name is None:
            raise ValueError("KMZ 안에서 .kml 파일을 찾지 못했습니다.")

        print(f"[DEBUG] 사용될 KML 파일: {kml_name}")

        # 2) 그 kml 파일을 파싱
        with z.open(kml_name) as f:
            tree = ET.parse(f)

    root = tree.getroot()

    # 3) 네임스페이스 자동 감지
    #    예) root.tag == '{http://www.opengis.net/kml/2.2}kml'
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0].strip("{")
    else:
        ns_uri = "http://www.opengis.net/kml/2.2"  # 일반적인 기본값

    print(f"[DEBUG] KML namespace: {ns_uri}")

    ns = {"kml": ns_uri}

    coords_list = []

    # 4) 모든 LineString 안의 <coordinates> 태그에서 좌표 읽기
    for ls in root.findall(".//kml:LineString", ns):
        coords_elem = ls.find("kml:coordinates", ns)
        if coords_elem is None or not coords_elem.text:
            continue

        # "lon,lat,alt lon,lat,alt ..." 형식
        for item in coords_elem.text.strip().split():
            parts = item.split(",")
            if len(parts) < 2:
                continue
            lon_str, lat_str = parts[0], parts[1]
            lat = float(lat_str)
            lon = float(lon_str)
            coords_list.append((lat, lon))

    print(f"[DEBUG] 추출된 좌표 개수: {len(coords_list)}")
    return coords_list


if __name__ == "__main__":
    print("[DEBUG] map.py 시작")  # 프로그램 시작 로그

    # 현재 파일(map.py)이 있는 폴더 기준 경로
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print("[DEBUG] BASE_DIR:", BASE_DIR)
    print("[DEBUG] 현재 작업 디렉토리(cwd):", os.getcwd())

    # 같은 폴더에 있는 route.kmz 사용
    kmz_file = os.path.join(BASE_DIR, "route.kmz")
    print("[DEBUG] 예상 KMZ 경로:", kmz_file)

    if not os.path.exists(kmz_file):
        print("[ERROR] KMZ 파일을 찾을 수 없습니다!")
        input("엔터를 누르면 종료합니다...")  # 창이 바로 닫히지 않게
        raise FileNotFoundError(f"KMZ 파일을 찾을 수 없습니다: {kmz_file}")

    try:
        # 좌표 리스트 읽기
        points = load_kmz_coords(kmz_file)

        print("총 좌표 개수:", len(points))
        print("앞 5개:", points[:5])

        # 같은 폴더에 route_points.py 로 저장
        output_path = os.path.join(BASE_DIR, "route_points.py")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 이 파일은 map.py에서 자동 생성되었습니다.\n")
            f.write("PRESET_POINTS = [\n")
            for lat, lon in points:
                f.write(f"    ({lat:.8f}, {lon:.8f}),\n")
            f.write("]\n")

        print(f"좌표 리스트를 {output_path} 에 PRESET_POINTS 로 저장했습니다.")

    except Exception as e:
        print("[ERROR] 실행 중 오류 발생:", e)

    input("엔터를 누르면 종료합니다...")  # 창 닫히기 전에 멈춤
