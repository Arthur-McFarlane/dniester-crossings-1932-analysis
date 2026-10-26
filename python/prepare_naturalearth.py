"""Clip the Natural Earth 1:10m layers used by the maps to the area they show, so the
repository holds small files. Natural Earth (https://www.naturalearthdata.com) is in the
public domain. Run once from the repository root with the full 10m GeoJSON files in a folder
given as the first argument:  python python/prepare_naturalearth.py /path/to/naturalearth"""
import json, sys
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path("data/naturalearth")
BOX = (25.0, 63.0, 42.0, 59.0)  # lon min, lon max, lat min, lat max

def clip(ring, box):
    """Sutherland-Hodgman clipping of one polygon ring to a rectangle."""
    x0, x1, y0, y1 = box
    edges = [(lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
             (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))]
    out = [tuple(p[:2]) for p in ring]
    for inside, cut in edges:
        pts, out = out, []
        if not pts: break
        prev = pts[-1]
        for cur in pts:
            if inside(cur):
                if not inside(prev): out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
            prev = cur
    return [list(p) for p in out] + ([list(out[0])] if out else [])

def polygons(name):
    feats = []
    for f in json.load(open(SRC / name))["features"]:
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            r = clip(poly[0], BOX)
            if len(r) > 3:
                feats.append({"type": "Feature", "properties": {},
                              "geometry": {"type": "Polygon", "coordinates": [[[round(x, 5), round(y, 5)] for x, y in r]]}})
    return {"type": "FeatureCollection", "features": feats}

OUT.mkdir(parents=True, exist_ok=True)
json.dump(polygons("ne_10m_land.geojson"), open(OUT / "land.geojson", "w"))
json.dump(polygons("ne_10m_lakes.geojson"), open(OUT / "lakes.geojson", "w"))
riv = [f for f in json.load(open(SRC / "ne_10m_rivers_lake_centerlines.geojson"))["features"]
       if f["properties"].get("name") == "Dniester"]
for f in riv: f["properties"] = {"name": "Dniester"}
json.dump({"type": "FeatureCollection", "features": riv}, open(OUT / "dniester.geojson", "w"))
print("written to", OUT)
