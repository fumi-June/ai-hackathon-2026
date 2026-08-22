#!/usr/bin/env python3
"""ヤマスキップにルートを追加するツール。OSM(Overpass)からルート名で検索して
docs/hikemap/routes.geojson に追記する。stdlibのみ・キー不要。

使い方:
  # 1) まず候補を検索（書き込みなし）
  python3 tools/add_route.py --search "稲荷山"

  # 2) 追加（relation/way両方から名前一致を集めてMultiLineStringで追記）
  python3 tools/add_route.py "稲荷山" --area okutama --name "高尾山稲荷山コース"

  # bbox指定（デフォルトは関東山地全域 35.3,138.5,36.2,139.5 = S,W,N,E）
  python3 tools/add_route.py "表参道" --area chichibu --bbox 35.90,138.90,35.95,139.00

注意: OSMに名前付き線形が無いルート（例: 両神山日向大谷・武甲山表参道）は
検索0件になる。その場合はこのツールでは追加できない（座標の捏造はしない）。
"""
import argparse, json, sys, urllib.parse, urllib.request
from pathlib import Path

OVERPASS = "https://overpass-api.de/api/interpreter"
GEOJSON = Path(__file__).resolve().parent.parent / "docs" / "hikemap" / "routes.geojson"
DEFAULT_BBOX = "35.3,138.5,36.2,139.5"  # S,W,N,E
AREAS = ("tanzawa", "okutama", "chichibu")


def overpass(query: str) -> dict:
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(OVERPASS, data=data,
                                 headers={"User-Agent": "hikemap-add-route/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch(name_re: str, bbox: str, with_geom: bool) -> list:
    out = "geom" if with_geom else "tags"
    q = (f'[out:json][timeout:40];('
         f'relation["route"="hiking"]["name"~"{name_re}"]({bbox});'
         f'way["highway"~"path|footway|track|steps"]["name"~"{name_re}"]({bbox});'
         f');out {out};')
    return overpass(q).get("elements", [])


def thin(coords):
    out = [coords[0]] + coords[1:-1:3] + [coords[-1]] if len(coords) > 4 else coords
    return [[round(x, 5), round(y, 5)] for x, y in out]


def lines_of(elements) -> list:
    lines = []
    for el in elements:
        if el["type"] == "way":
            g = el.get("geometry") or []
            if len(g) >= 2:
                lines.append(thin([[p["lon"], p["lat"]] for p in g]))
        elif el["type"] == "relation":
            for m in el.get("members", []):
                g = m.get("geometry")
                if m.get("type") == "way" and g and len(g) >= 2:
                    lines.append(thin([[p["lon"], p["lat"]] for p in g]))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="OSMのname正規表現（例: 稲荷山|６号路）")
    ap.add_argument("--search", action="store_true", help="候補一覧のみ（書き込みなし）")
    ap.add_argument("--area", choices=AREAS, help="表示エリア（追加時必須）")
    ap.add_argument("--name", help="地図上の表示名（省略時はOSM名を使用）")
    ap.add_argument("--bbox", default=DEFAULT_BBOX, help="S,W,N,E")
    a = ap.parse_args()

    if a.search:
        els = fetch(a.query, a.bbox, with_geom=False)
        if not els:
            print("0件。OSMに名前付き線形なし（bbox/表記ゆれも確認を）"); return
        for el in els:
            print(f'{el["type"]} {el["id"]}  {el.get("tags", {}).get("name", "無名")}')
        return

    if not a.area:
        sys.exit("追加には --area tanzawa|okutama|chichibu が必要（--searchで下見可）")
    els = fetch(a.query, a.bbox, with_geom=True)
    lines = lines_of(els)
    if not lines:
        sys.exit(f'"{a.query}" は0件。--search で表記を確認するか、bboxを調整')

    name = a.name or next((e.get("tags", {}).get("name") for e in els
                           if e.get("tags", {}).get("name")), a.query)
    gj = json.load(open(GEOJSON))
    if any(f["properties"]["name"] == name for f in gj["features"]):
        sys.exit(f'"{name}" は既に存在。--name で別名を指定して')
    gj["features"].append({"type": "Feature",
        "geometry": {"type": "MultiLineString", "coordinates": lines},
        "properties": {"name": name, "area": a.area}})
    json.dump(gj, open(GEOJSON, "w"), ensure_ascii=False, separators=(",", ":"))
    pts = sum(len(l) for l in lines)
    print(f'追加: {name} ({a.area}, {len(lines)}区間/{pts}点) → 合計{len(gj["features"])}本')
    print("公開するには: git add docs/hikemap/routes.geojson && git commit && git push")


if __name__ == "__main__":
    main()
